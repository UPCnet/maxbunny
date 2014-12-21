# -*- coding: utf-8 -*-
from apnsclient import APNs
from apnsclient import Message
from apnsclient import Session
from gcmclient import GCM
from gcmclient import JSONMessage
from maxbunny.consumer import BunnyConsumer, BunnyMessageCancel
from maxcarrot.message import RabbitMessage
from maxbunny.utils import extract_domain
from maxbunny.utils import normalize_message

import re
from copy import deepcopy


class PushConsumer(BunnyConsumer):
    """
    """
    name = 'push'
    queue = 'push'

    def configure(self, runner):
        self.ios_session = Session()
        self.ios_push_certificate_file = runner.cloudapis.get('push', 'push_certificate_file')
        self.android_push_api_key = runner.cloudapis.get('push', 'android_push_api_key')

    def process(self, rabbitpy_message):
        """
        """
        if not self.ios_push_certificate_file and not self.android_push_api_key:
            raise BunnyMessageCancel('PUSH keys not configured')

        packed_message = rabbitpy_message.json()
        message = normalize_message(RabbitMessage.unpack(packed_message))

        message_object = message.get('object', None)
        message_data = message.get('data', {})
        message_data_id = message_data.get('id', None)
        message_data_text = message_data.get('text', '')

        message_user = message.get('user', {})
        message_username = message_user.get('username', None)

        if not message_username:
            raise BunnyMessageCancel('Missing or empty user data')

        tokens = None
        tokens_by_platform = {}
        usernames_by_token = {}

        domain = extract_domain(message)
        client = self.clients[domain]

        # Client will be None only if after determining the domain (or getting the default),
        # no client could be found matching that domain
        if client is None:
            raise BunnyMessageCancel('Unknown domain "unknown"'.format(domain))

        # Forward the routing key to the mobile apps as "destination" field
        match_destination = re.match(r'(\w+).?(?:messages|notifications)?', rabbitpy_message.routing_key)
        message['destination'] = match_destination.groups()[0] if match_destination else None

        push_message, tokens = self.handle_message(message, client)

        if not tokens:
            raise BunnyMessageCancel('No tokens received', notify=False)

        # Map user and tokens, indexed by platform and token
        for token in tokens:
            tokens_by_platform.setdefault(token.get('platform'), [])
            usernames_by_token.setdefault(token.get('token'), [])
            usernames_by_token[token.get('token')].append(token.get('username'))

            is_debug_message = '#pushdebug' in message_data_text
            token_is_from_sender = token.get('username') == message_username
            token_is_duplicated = token.get('token') in tokens_by_platform[token.get('platform')]

            # Do not append token to sender unless #debug hashtag included
            # and add it only if it's not already in the list
            # use case: two users within a conversation, both logged in the same device. Shit happens

            if (is_debug_message or not token_is_from_sender) and not token_is_duplicated:
                tokens_by_platform[token.get('platform')].append(token.get('token'))

        processed_tokens = []
        processed_tokens += self.send_ios_push_notifications(tokens_by_platform.get('iOS', []), push_message.packed)
        processed_tokens += self.send_android_push_notifications(tokens_by_platform.get('android', []), push_message.packed)

        # If we reach here, push messages had been sent without major failures
        # But may have errors on particular tokens. Let's log successes and failures of
        # all processed tokens, showing the associated user(s) (not the token), for mental sanity.
        succeed = []
        failed = []

        succeeded_tokens = 0

        # Construct a namespace reference id, that includes the domain and
        # the context type & id on the source max server
        mid = message_data_id if message_data_id else '<missing-id>'
        target = 'activity' if message_object == 'activity' else 'messages'
        message_full_id = '{}.{}.{}'.format(target, push_message['destination'], mid)

        # Aggregate data from both success and failures
        for platform, token, error in processed_tokens:
            token_usernames = usernames_by_token.get(token, [])
            usernames_string = ','.join(token_usernames)
            if len(token_usernames) > 1:
                self.logger.warning('[{}] {} token {} shared by {}'.format(domain, platform, token, usernames_string))

            if error is None:
                succeed += token_usernames
                succeeded_tokens += 1
            else:
                failed.append((platform, usernames_string, error))

        # Log once for all successes
        if succeed:
            self.logger.info('[{}] SUCCEDED {}/{} push {} to {}'.format(domain, succeeded_tokens, len(processed_tokens), message_full_id, ','.join(succeed)))

        for platform, username, reason in failed:
            self.logger.warning('[{}] FAILED {} push {} to {}: {}'.format(domain, platform, message_full_id, username, reason))

        return processed_tokens

    def handle_message(self, message, client):
        message_object = message.get('object', None)
        if message_object is None:
            raise BunnyMessageCancel('The received message has an unknown object type')

        message_processor_method_name = 'process_{}_object'.format(message_object)
        method = getattr(self, message_processor_method_name)
        return method(message, client)

    def process_activity_object(self, message, client):
        """
            Post or comment from a context
        """
        if message['destination'] is None:
            raise BunnyMessageCancel('The received message is not from a valid context')

        tokens = client.contexts[message['destination']].tokens.get()
        message.setdefault('data', {})
        message['data']['alert'] = u'{user[displayname]}: '.format(**message)
        return message, tokens

    def process_message_object(self, message, client):
        """
            Message from a conversation
        """
        if message['destination'] is None:
            raise BunnyMessageCancel('The received message is not from a valid conversation')

        tokens = client.conversations[message['destination']].tokens.get()
        message.setdefault('data', {})
        message['data']['alert'] = u'{user[displayname]}: '.format(**message)
        return message, tokens

    def process_conversation_object(self, message, client):
        """
            Conversation creation object
        """
        if message['destination'] is None:
            raise BunnyMessageCancel('The received message is not from a valid conversation')

        messages = {
            'add': {
                'en': u"{user[username]} started a chat".format(**message),
                'es': u"{user[username]} ha iniciado un chat".format(**message),
                'ca': u"{user[username]} ha iniciat un xat".format(**message),
            },
            'refresh': {
                'en': u"You have received an image".format(**message),
                'es': u"Has recibido una imagen".format(**message),
                'ca': u"Has rebut una imatge".format(**message),
            }
        }

        action = message.get('action', None)
        # Temporary WORKAROUND
        # Rewrite add and refresh covnersation messages with regular text messages explaining it
        try:
            if action in ['add', 'refresh']:
                message.action = 'ack'
                message.object = 'message'
                message.setdefault('data', {})
                message['data']['text'] = messages[action][client.metadata['language']]
                message['data']['alert'] = ''
        except:
            raise BunnyMessageCancel('Cannot find a message to rewrite {} conversation'.format(action))

        tokens = client.conversations[message['destination']].tokens.get()

        return message, tokens

    def send_ios_push_notifications(self, tokens, message):
        """
        """
        if not tokens:
            return []

        # Remove unvalid tokens
        sanitized_tokens = [token for token in tokens if re.match(r'^[a-fA-F0-9]{64}$', token, re.IGNORECASE)]

        # Remove unnecessary fields
        extra = deepcopy(message)
        extra.pop('d', None)
        extra.pop('g', None)
        if 'u' in extra:
            if 'd' in extra['u'] and isinstance(extra['u'], dict):
                del extra['u']['d']

        # Prepare the push message
        push_message = Message(
            sanitized_tokens,
            alert=message['d']['alert'] + message['d']['text'],
            badge=1,
            sound='default',
            extra=extra)

        # Send the message.
        con = self.ios_session.get_connection("push_production", cert_file=self.ios_push_certificate_file)
        srv = APNs(con)
        res = srv.send(push_message)

        # If APNS doesn't crash for unknown reasons,
        # collect result for each push sent
        # Exceptions caused by APNS failure or code bugs will be
        # catched in a upper leve

        processed_tokens = []

        for token in tokens:
            if token in res.failed:
                processed_tokens.append(('ios', token, 'ERR={} {}'.format(*res.failed[token])))
            else:
                processed_tokens.append(('ios', token, None))

        return processed_tokens

    def send_android_push_notifications(self, tokens, message):
        if not tokens:
            return []

        # Prepare push message
        data = {'message': message, 'int': 10}
        multicast = JSONMessage(tokens, data, collapse_key='my.key', dry_run=False)

        # Send push message
        gcm = GCM(self.android_push_api_key)
        res = gcm.send(multicast)

        # XXX TODO  Retry on failed items
        # if res.needs_retry():
        #     # construct new message with only failed regids
        #     retry_msg = res.retry()
        #     # you have to wait before attemting again. delay()
        #     # will tell you how long to wait depending on your
        #     # current retry counter, starting from 0.
        #     print "Wait or schedule task after %s seconds" % res.delay(retry)
        #     # retry += 1 and send retry_msg again

        processed_tokens = []
        for token in tokens:
            if token in self.success:
                processed_tokens.append(('ios', token, None))

            elif token in res.unavailable:
                processed_tokens.append(('android', token, 'Unavailable'))

            elif token in res.not_registered:
                processed_tokens.append(('android', token, 'Not Registered'))
                # probably app was uninstalled
                # self.logger.info(u"[Android] Invalid %s from database" % reg_id)

            elif token in res.failed:
                processed_tokens.append(('android', token, res.failed[token]))
                # unrecoverably failed, these ID's will not be retried
                # consult GCM manual for all error codes
                # self.logger.info(u"[Android] Should remove %s because %s" % (reg_id, err_code))

            # if token in self.canonical:
                # Update registration ids

        return processed_tokens

__consumer__ = PushConsumer
