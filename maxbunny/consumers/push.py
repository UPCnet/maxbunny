# -*- coding: utf-8 -*-
from maxbunny.consumer import BunnyConsumer
from maxbunny.consumer import BunnyMessageCancel
from maxbunny.utils import extract_domain
from maxbunny.utils import normalize_message
from maxcarrot.message import RabbitMessage

from apnsclient import APNs
from apnsclient import Message
from apnsclient import Session
from copy import deepcopy
from gcmclient import GCM
from gcmclient import JSONMessage

from pyfcm import FCMNotification
from bs4 import BeautifulSoup

import re


class PushConsumer(BunnyConsumer):
    """
    """
    name = 'push'
    queue = 'push'

    def configure(self, runner):
        self.ios_session = Session()
        self.ios_push_certificate_file = runner.cloudapis.get('push', 'push_certificate_file')
        self.android_push_api_key = runner.cloudapis.get('push', 'android_push_api_key')
        self.firebase_push_api_key = runner.cloudapis.get('push', 'firebase_push_api_key')

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
        client = self.get_domain_client(domain)

        # Forward the routing key to the mobile apps as "destination" field
        match_destination = re.match(r'(\w+).?(?:messages|notifications)?', rabbitpy_message.routing_key)
        message['destination'] = match_destination.groups()[0] if match_destination else None

        push_message, tokens = self.handle_message(message, client)

        if not tokens:
            raise BunnyMessageCancel('No tokens received', notify=False)

        # Map user and tokens, indexed by platform and token
        for token_info in tokens:
            token_platform = token_info.get('platform').lower()
            token = token_info.get('token')
            token_owner = token_info.get('username')

            tokens_by_platform.setdefault(token_platform, [])
            usernames_by_token.setdefault(token, [])
            usernames_by_token[token].append(token_owner)

            is_debug_message = '#pushdebug' in message_data_text
            token_is_from_sender = token_owner == message_username
            token_is_duplicated = token in tokens_by_platform[token_platform]

            # Do not append token to sender unless #debug hashtag included
            # and add it only if it's not already in the list
            # use case: two users within a conversation, both logged in the same device. Shit happens

            if (is_debug_message or not token_is_from_sender) and not token_is_duplicated:
                tokens_by_platform[token_platform].append(token)

        processed_tokens = []

        #Notificaciones push APP uTalk antigua
        processed_tokens += self.send_ios_push_notifications(tokens_by_platform.get('ios', []), push_message.packed)
        processed_tokens += self.send_android_push_notifications(tokens_by_platform.get('android', []), push_message.packed)

        # Notificaciones push APP uTalk nueva
        processed_tokens += self.send_firebase_push_notifications((tokens_by_platform.get('ios', []) + tokens_by_platform.get('android', [])), push_message.packed)

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
            if platform != 'firebase':
                token_usernames = usernames_by_token.get(token, [])
                usernames_string = ','.join(token_usernames)
                if len(token_usernames) > 1:
                    self.logger.warning('[{}] {} token {} shared by {}'.format(domain, platform, token, usernames_string))

                if error is None:
                    succeed += token_usernames
                    succeeded_tokens += 1
                else:
                    #client.tokens[token].delete()
                    failed.append((platform, usernames_string, error))
            else:
                #Este try solo sirve para los test de las notificaciones push
                try:
                    error = error.response
                except:
                    pass

                self.logger.info('[{}] RESPONSE {} push : {}'.format(domain, platform, error))

        # Log once for all successes
        if succeed:
            unique_sorted_users = sorted(list(set(succeed)))
            self.logger.info('[{}] SUCCEDED {}/{} push {} to {}'.format(domain, succeeded_tokens, len(processed_tokens) - 1, message_full_id, ','.join(unique_sorted_users)))

        for platform, username, reason in failed:
            self.logger.warning('[{}] FAILED {} push {} to {}: {}'.format(domain, platform, message_full_id, username, reason))

        return processed_tokens

    def handle_message(self, message, client):
        message_object = message.get('object', None)
        if message_object is None:
            raise BunnyMessageCancel('The received message has an unknown object type')

        #Como es el specification.json del maxcarrot modificamos la letra id del object comment para que llegaran ahora el objecto es una actividad
        #para poder añadir literal a la notificación push, miro si es un comentario y asi ejecuto el process_comment_object y no el process_activity_object
        if 'commentid' in message['data']:
            message_object = u'comment'

        message_processor_method_name = 'process_{}_object'.format(message_object)
        method = getattr(self, message_processor_method_name)
        return method(message, client)

    def process_activity_object(self, message, client):
        """
            An activity has been posted on a context
        """
        if message['destination'] is None:
            raise BunnyMessageCancel('The received message is not from a valid context')

        values = {
            'add': {
                'en': [u"I\'ve added", u"I\'ve modified"],
                'es': [u"He añadido", u"He modificado"],
                'ca': [u"He afegit", u"He modificat"],
            },
        }
        messages = {
            'add': {
                'en': u"I\'ve published a new activity: ".format(**message),
                'es': u"He publicado una nueva actividad: ".format(**message),
                'ca': u"He publicat una nova activitat: ".format(**message),
            },
            'image': {
                'en': u"Image".format(**message),
                'es': u"Imagen".format(**message),
                'ca': u"Imatge".format(**message),
            }
        }

        action = message.get('action', None)

        if message['data']['text'] == u'Add image':
            message['data']['text'] = messages['image'][client.metadata['language']]
            message['data']['alert'] = u'{user[displayname]}: '.format(**message)
        else:
            # Si solo es una notificacion diretamente en el POST añadir literal "He publicado una nueva actividad: " y el texto que has añadido
            if not message['data']['text'].startswith(tuple(values[action][client.metadata['language']])):
                message['data']['text'] = messages[action][client.metadata['language']] + message['data']['text']
            else:
                # Quitar la url del bit.ly para que no aparezca en el push
                text = re.sub(r'a http?:\/\/.*[\r\n]*', '', message['data']['text'])
                message['data']['text'] = text

            message.setdefault('data', {})
            message['data']['alert'] = u'{user[displayname]}: '.format(**message)

        tokens = client.contexts[message['destination']].tokens.get()
        return message, tokens

    def process_comment_object(self, message, client):
        """
            A message has been posted on a context activity
        """
        if message['destination'] is None:
            raise BunnyMessageCancel('The received message is not from a valid context')

        messages = {
            'add': {
                'en': u"Added the comment: ".format(**message),
                'es': u"He añadido el comentario: ".format(**message),
                'ca': u"He afegit el comentari: ".format(**message),
            },
        }

        action = message.get('action', None)

        # Si se añade un comentario, añadir en la notificación push el literal "He añadido el comentario: " + el comentario
        try:
            if action in ['add']:
                message['data']['text'] = messages[action][client.metadata['language']] + message['data']['text']
        except:
            raise BunnyMessageCancel('Cannot find a message to rewrite {} conversation'.format(action))

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

        messages = {
            'image': {
                'en': u"Image".format(**message),
                'es': u"Imagen".format(**message),
                'ca': u"Imatge".format(**message),
            }
        }

        if message['data']['text'] == u'Add image':
            message['data']['text'] = messages['image'][client.metadata['language']]
            message['data']['alert'] = u'{user[displayname]}: '.format(**message)
        else:
            message.setdefault('data', {})
            message['data']['alert'] = u'{user[displayname]}: '.format(**message)

        tokens = client.conversations[message['destination']].tokens.get()
        return message, tokens

    def process_conversation_object(self, message, client):
        """
            Conversation creation object
        """
        if message['destination'] is None:
            raise BunnyMessageCancel('The received message is not from a valid conversation')

        messages = {
            'add': {
                'en': u"Started a chat".format(**message),
                'es': u"Ha iniciado un chat".format(**message),
                'ca': u"Ha iniciat un xat".format(**message),
            },
            'refresh': {
                'en': u"You have received an image".format(**message),
                'es': u"Has recibido una imagen".format(**message),
                'ca': u"Has rebut una imatge".format(**message),
            },
            'image': {
                'en': u"Image".format(**message),
                'es': u"Imagen".format(**message),
                'ca': u"Imatge".format(**message),
            }
        }

        action = message.get('action', None)

        # Temporary WORKAROUND
        # Rewrite add and refresh covnersation messages with regular text messages explaining it
        try:
            if action in ['add', 'refresh']:
                message.action = 'ack'
                message.object = 'message'

                if message['data'] == {}:
                    message.setdefault('data', {})
                    message['data']['text'] = messages[action][client.metadata['language']]
                    message['data']['alert'] = ''
                else:
                    if 'conversation_id' in message['data']:
                        if message['data']['text'] == u'Add image':
                            message['data']['text'] = messages['image'][client.metadata['language']]
                            message['data']['alert'] = u'{user[displayname]}: '.format(**message)
                        else:
                            message['data']['text'] = message['data']['creator'] + ': ' + message['data']['text']
                            message['data']['alert'] = u'{user[displayname]}: '.format(**message)
                    else:
                        message['data']['text'] = message['data']['text']
                        message['data']['alert'] = ''
        except:
            raise BunnyMessageCancel('Cannot find a message to rewrite {} conversation'.format(action))

        tokens = client.conversations[message['destination']].tokens.get()

        return message, tokens

    def get_message_object(self, message):
        message = normalize_message(RabbitMessage.unpack(message))
        if message['user']['displayname'] == '':
            message_title = message['user']['username']
        else:
            message_title = message['user']['displayname']

        #Ejecuto el BeautifulSoup sobre el message para quitar todos los tags html <b> <i> porque el push no los sabe mostrar
        #He probado con *texto* para negritas como hace whatssap pero tampoco lo sabe tratar
        if message['object'] == 'activity' and message['action'] == 'add':
            message_body = BeautifulSoup(message['data']['text']).text
        elif message['object'] == 'conversation' and (message['action'] == 'add' or message['action'] == 'refresh'):
            message_body = BeautifulSoup(message['data']['text']).text
        elif message['object'] == 'message' and (message['action'] == 'ack' or message['action'] == 'add'):
            message_body = BeautifulSoup(message['data']['text']).text
        else:
            message_body = ''


        return message_title, message_body

    def send_firebase_push_notifications(self, tokens, message):
        """
        """

        if not tokens:
            return []

        # Send the message Firebase
        push_service = FCMNotification(api_key=self.firebase_push_api_key)
        message_title, message_body  = self.get_message_object(message)

        processed_tokens = []


        if message_body != '':
            data = {'message': message}

            res = push_service.notify_multiple_devices(registration_ids=tokens, message_title=message_title, message_body=message_body, data_message=data, content_available=True)

            # If APNS doesn't crash for unknown reasons,
            # collect result for each push sent
            # Exceptions caused by APNS failure or code bugs will be
            # catched in a upper level

            # OJO como por ahora en Firebase no hemos encontrado que se puedan procesar que
            # notificaciones han fallado (tokens failed) no procesamos nada y enviamos la respuesta push
            processed_tokens.append(('firebase', tokens, res))

        return processed_tokens

    def send_ios_push_notifications(self, tokens, message):
        """
        """
        if not tokens:
            return []

        # Remove unvalid tokens
        sanitized_tokens = [token for token in tokens if re.match(r'^[a-fA-F0-9]{64}$', token, re.IGNORECASE)]

        # Remove unnecessary fields
        extra = deepcopy(message)
        extra.pop('d', None)        # Remove data field
        extra.pop('g', None)        # Remove uuid field
        extra['u'].pop('d', None)   # Remove displayname field

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
        # catched in a upper level

        processed_tokens = []

        for token in tokens:
            if token in res.failed:
                processed_tokens.append(('ios', token, 'ERR={} {}'.format(*res.failed[token])))
            else:
                processed_tokens.append(('ios', token, None))

        return processed_tokens

    def send_android_push_notifications(self, tokens, message):
        """
        """
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

        def has_token_in(status, token):
            """
                Safe check that token in contained in a res.<status> attribute
            """
            if not hasattr(res, status):
                return False
            return token in getattr(res, status)

        processed_tokens = []
        for token in tokens:
            if has_token_in('success', token):
                processed_tokens.append(('ios', token, None))

            elif has_token_in('unavailable', token):
                processed_tokens.append(('android', token, 'Unavailable'))

            elif has_token_in('not_registered', token):
                processed_tokens.append(('android', token, 'Not Registered'))
                # probably app was uninstalled
                # self.logger.info(u"[Android] Invalid %s from database" % reg_id)

            elif has_token_in('failed', token):
                processed_tokens.append(('android', token, res.failed[token]))
                # unrecoverably failed, these ID's will not be retried
                # consult GCM manual for all error codes
                # self.logger.info(u"[Android] Should remove %s because %s" % (reg_id, err_code))

            # if token in self.canonical:
                # Update registration ids

        return processed_tokens

__consumer__ = PushConsumer
