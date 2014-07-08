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
        packed_message = rabbitpy_message.json()
        message = RabbitMessage.unpack(packed_message)

        message_object = message.get('object', None)
        tokens = None
        tokens_by_platform = {}

        # messages from a conversation
        if message_object == 'message':
            conversation_id = re.search(r'(\w+).(?:messages|notifications)', rabbitpy_message.routing_key).groups()[0]
            domain = extract_domain(message)
            client = self.clients[domain]

            # Client will be None only if after determining the domain (or getting the default),
            # no client could be found matching that domain
            if client is None:
                raise BunnyMessageCancel('Unknown domain {}'.format(domain))

            if conversation_id is None:
                raise BunnyMessageCancel('The message received is not from a valid conversation')

            tokens = client.conversations[conversation_id].tokens.get()

        # messages from a context
        elif message_object == 'activity':
            context_id = rabbitpy_message.routing_key
            domain = extract_domain(message)
            client = self.clients[domain]

            # Client will be None only if after determining the domain (or getting the default),
            # no client could be found matching that domain
            if client is None:
                raise BunnyMessageCancel('Unknown domain {}'.format(domain))

            if context_id is None:
                raise BunnyMessageCancel('The activity received is not from a valid context')

            tokens = client.contexts[context_id].tokens.get()

        else:
            raise BunnyMessageCancel('The activity received has an unknown object type')

        if tokens is None:
            raise BunnyMessageCancel('No tokens received')

        for token in tokens:
            # TODO: On production, not send notification to sender
            # if token.get('username') != message.get('user', {}).get('username'):
            tokens_by_platform.setdefault(token.get('platform'), []).append(token.get('token'))

        if self.ios_push_certificate_file and tokens_by_platform.get('iOS', []):
            try:
                user_displayname = message['user'].get('displayname', message['user'].get('username', ''))
                self.send_ios_push_notifications(tokens_by_platform['iOS'], '{}: {}'.format(user_displayname, message['data']['text']), packed_message)
            except Exception as error:
                exception_class = '{}.{}'.format(error.__class__.__module__, error.__class__.__name__)
                return_message = "iOS device push failed: {0}, reason: {1} {2}".format(tokens_by_platform['iOS'], exception_class, error.message)
                raise BunnyMessageCancel(return_message)

        if self.android_push_api_key and tokens_by_platform.get('android', []):
            try:
                self.send_android_push_notifications(tokens_by_platform['android'], packed_message)
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
        if 'd' in extra['u']:
            del extra['u']['d']

        push_message = Message(tokens, alert=alert, badge=1, sound='default', extra=extra)

        # Send the message.
        srv = APNs(con)
        res = srv.send(push_message)

        # Check failures. Check codes in APNs reference docs.
        for token, reason in res.failed.items():
            code, errmsg = reason
            return_message = "[iOS] Device push failed: {0}, reason: {1}".format(token, errmsg)
            tokens.remove(token)
            self.logger.info(return_message)

        return_message = "[iOS] Successfully sent {} to {}.".format(push_message.alert, tokens)
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
                    self.logger.info("[Android] Successfully sent %s as %s" % (reg_id, msg_id))

                # # update your registration ID's
                # for reg_id, new_reg_id in res.canonical.items():
                #     print "Replacing %s with %s in database" % (reg_id, new_reg_id)

                # probably app was uninstalled
                for reg_id in res.not_registered:
                    self.logger.info("[Android] Invalid %s from database" % reg_id)

                # unrecoverably failed, these ID's will not be retried
                # consult GCM manual for all error codes
                for reg_id, err_code in res.failed.items():
                    self.logger.info("[Android] Should remove %s because %s" % (reg_id, err_code))

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
            self.logger.info("[Android] Your Google API key is rejected")
        except ValueError, e:
            # probably your extra options, such as time_to_live,
            # are invalid. Read error message for more info.
            self.logger.info("[Android] Invalid message/option or invalid GCM response")
            print e.args[0]
        except Exception:
            # your network is down or maybe proxy settings
            # are broken. when problem is resolved, you can
            # retry the whole message.
            self.logger.info("[Android] Something wrong with requests library")


__consumer__ = PushConsumer
