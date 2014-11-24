# -*- coding: utf-8 -*-
from apnsclient import APNs
from apnsclient import Message
from apnsclient import Session
from gcmclient import GCM
from gcmclient import GCMAuthenticationError
from gcmclient import JSONMessage
from maxbunny.consumer import BunnyConsumer, BunnyMessageCancel
from maxcarrot.message import RabbitMessage
from maxbunny.utils import extract_domain

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
            return
            raise BunnyMessageCancel('PUSH keys not configured')

        packed_message = rabbitpy_message.json()
        message = RabbitMessage.unpack(packed_message)

        # Forward the routing key to the mobile apps
        message['destination'] = rabbitpy_message.routing_key

        message_object = message.get('object', None)
        message_action = message.get('action', None)
        message_user = message.get('user', {})
        if isinstance(message_user, dict):
            message_username = message_user.get('username', "")
            message_display_name = message.get('user', {}).get('displayname', message_username)
        else:
            message_username = message_user
            message_display_name = message_user

        prepend_user_in_alert = True

        tokens = None
        tokens_by_platform = {}

        domain = extract_domain(message)
        client = self.clients[domain]

        # Client will be None only if after determining the domain (or getting the default),
        # no client could be found matching that domain
        if client is None:
            raise BunnyMessageCancel('Unknown domain {}'.format(domain))

        # messages from a conversation
        if message_object in ['message', 'conversation ']:
            conversation_id = re.search(r'(\w+).(?:messages|notifications)', rabbitpy_message.routing_key).groups()[0]

            if conversation_id is None:
                raise BunnyMessageCancel('The message received is not from a valid conversation')

            tokens = client.conversations[conversation_id].tokens.get()

        # messages from a context
        elif message_object == 'activity':
            context_id = rabbitpy_message.routing_key

            if context_id is None:
                raise BunnyMessageCancel('The activity received is not from a valid context')

            tokens = client.contexts[context_id].tokens.get()

        # messages from a context
        elif message_object == 'conversation':
            conversation_id = re.search(r'(\w+).(?:messages|notifications)', rabbitpy_message.routing_key).groups()[0]
            if conversation_id is None:
                raise BunnyMessageCancel('The activity received is not from a valid context')

            tokens = client.conversations[conversation_id].tokens.get()

            messages = {
                'add': {
                    'en': u"{} started a chat".format(message_display_name),
                    'es': u"{} ha iniciado un chat".format(message_display_name),
                    'ca': u"{} ha iniciat un xat".format(message_display_name),
                },
                'refresh': {
                    'en': u"You have received an image".format(message_display_name),
                    'es': u"Has recibido una imagen".format(message_display_name),
                    'ca': u"Has rebut una imatge".format(message_display_name),
                }

            }

            # Temporary WORKAROUND
            # Rewrite add and refresh covnersation messages with regular text messages explaining it
            try:
                if message_action in ['add', 'refresh']:
                    prepend_user_in_alert = False
                    message.action = 'ack'
                    message.object = 'message'
                    message.setdefault('data', {})
                    message['data']['text'] = messages[message_action][self.clients.get_client_language(domain)]
                    packed_message = message.packed
            except:
                raise BunnyMessageCancel('Cannot find a message to rewrite {} {}' .format(message_action, message_object))

            tokens = client.conversations[conversation_id].tokens.get()

        else:
            raise BunnyMessageCancel('The activity received has an unknown object type')

        if tokens is None:
            raise BunnyMessageCancel('No tokens received')

        for token in tokens:
            tokens_by_platform.setdefault(token.get('platform'), [])

            is_debug_message = '#pushdebug' in message.get('data', {}).get('text', '')
            token_is_from_sender = token.get('username') == message_username
            token_is_duplicated = token.get('token') in tokens_by_platform[token.get('platform')]

            # Do not append token to sender unless #debug hashtag included
            # and add it only if it's not already in the list
            # use case: two users within a conversation, both logged in the same device. Shit happens

            if (is_debug_message or not token_is_from_sender) and not token_is_duplicated:
                tokens_by_platform[token.get('platform')].append(token.get('token'))

        if self.ios_push_certificate_file and tokens_by_platform.get('iOS', []):
            try:
                message_text = message.get('data', {}).get('text', "")
                if prepend_user_in_alert:
                    alert_text = u'{}: {}'.format(message_display_name, message_text)
                else:
                    alert_text = message_text
                self.send_ios_push_notifications(tokens_by_platform['iOS'], alert_text, message.packed)
            except Exception as error:
                exception_class = '{}.{}'.format(error.__class__.__module__, error.__class__.__name__)
                return_message = "iOS device push failed: {0}, reason: {1} {2}".format(tokens_by_platform['iOS'], exception_class, error.message)
                raise BunnyMessageCancel(return_message)

        if self.android_push_api_key and tokens_by_platform.get('android', []):
            try:
                self.send_android_push_notifications(tokens_by_platform['android'], message.packed)
            except Exception as error:
                exception_class = '{}.{}'.format(error.__class__.__module__, error.__class__.__name__)
                return_message = "Android device push failed: {0}, reason: {1} {2}".format(tokens_by_platform['android'], exception_class, error.message)
                raise BunnyMessageCancel(return_message)

        return

    def send_ios_push_notifications(self, tokens, alert, message):
        con = self.ios_session.get_connection("push_production", cert_file=self.ios_push_certificate_file)
        extra = deepcopy(message)

        if 'd' in extra:
            del extra['d']
        if 'g' in extra:
            del extra['g']
        if 'u' in extra:
            if 'd' in extra['u'] and isinstance(extra['u'], dict):
                del extra['u']['d']

        push_message = Message(tokens, alert=alert, badge=1, sound='default', extra=extra)

        # Send the message.
        srv = APNs(con)
        res = srv.send(push_message)

        # Check failures. Check codes in APNs reference docs.
        for token, reason in res.failed.items():
            code, errmsg = reason
            return_message = u"[iOS] Device push failed: {0}, reason: {1}".format(token, errmsg)
            tokens.remove(token)
            self.logger.info(return_message)

        return_message = u"[iOS] Successfully sent {} to {}.".format(push_message.alert, tokens)
        self.logger.info(return_message)
        return return_message

    def send_android_push_notifications(self, tokens, message):
        gcm = GCM(self.android_push_api_key)

        # Construct (key => scalar) payload. do not use nested structures.
        data = {'message': message, 'int': 10}

        # Unicast or multicast message, read GCM manual about extra options.
        # It is probably a good idea to always use JSONMessage, even if you send
        # a notification to just 1 registration ID.
        # unicast = PlainTextMessage("registration_id", data, dry_run=True)
        multicast = JSONMessage(tokens, data, collapse_key='my.key', dry_run=False)

        try:
            # attempt send
            res_multicast = gcm.send(multicast)

            for res in [res_multicast]:
                # nothing to do on success
                for reg_id, msg_id in res.success.items():
                    self.logger.info(u"[Android] Successfully sent %s as %s" % (reg_id, msg_id))

                # # update your registration ID's
                # for reg_id, new_reg_id in res.canonical.items():
                #     print "Replacing %s with %s in database" % (reg_id, new_reg_id)

                # probably app was uninstalled
                for reg_id in res.not_registered:
                    self.logger.info(u"[Android] Invalid %s from database" % reg_id)

                # unrecoverably failed, these ID's will not be retried
                # consult GCM manual for all error codes
                for reg_id, err_code in res.failed.items():
                    self.logger.info(u"[Android] Should remove %s because %s" % (reg_id, err_code))

                # # if some registration ID's have recoverably failed
                # if res.needs_retry():
                #     # construct new message with only failed regids
                #     retry_msg = res.retry()
                #     # you have to wait before attemting again. delay()
                #     # will tell you how long to wait depending on your
                #     # current retry counter, starting from 0.
                #     print "Wait or schedule task after %s seconds" % res.delay(retry)
                #     # retry += 1 and send retry_msg again

        except GCMAuthenticationError:
            # stop and fix your settings
            self.logger.info(u"[Android] Your Google API key is rejected")
        except ValueError, e:
            # probably your extra options, such as time_to_live,
            # are invalid. Read error message for more info.
            self.logger.info(u"[Android] Invalid message/option or invalid GCM response")
            print e.args[0]
        except Exception:
            # your network is down or maybe proxy settings
            # are broken. when problem is resolved, you can
            # retry the whole message.
            self.logger.info(u"[Android] Something wrong with requests library")


__consumer__ = PushConsumer
