# -*- coding: utf-8 -*-
from apnsclient import APNs
from apnsclient import Message
from apnsclient import Session
from gcmclient import GCM
from gcmclient import GCMAuthenticationError
from gcmclient import JSONMessage
from maxbunny.consumer import BUNNY_NO_DOMAIN
from maxbunny.consumer import BunnyConsumer, BunnyMessageCancel
from maxcarrot.message import RabbitMessage

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

    def process(self, rabbitpy_message):
        """
        """
        unpacked_message = rabbitpy_message.json()
        message = RabbitMessage.unpack(rabbitpy_message.json())

        conversation_id = re.search(r'(\w+).messages', rabbitpy_message.routing_key).groups()[0]
        domain = message.get('domain', BUNNY_NO_DOMAIN)
        client = self.clients[domain]

        # #print 'push', self.id, message.body
        # if message.body in ['3', '6']:
        #     return BUNNY_REQUEUE
        # if message.body == '0':
        #     return BUNNY_CANCEL
        # return BUNNY_OK

        if conversation_id is None:
            self.logger.info('The message received is not a valid conversation')
            return BunnyMessageCancel()

        tokens = client.conversations[conversation_id].tokens.get()

        tokens_by_platform = {}

        for token in tokens:
            # TODO: On production, not send notification to sender
            # if token.get('username') != self.message.get('username'):
            tokens_by_platform.setdefault(token.get('platform'), []).append(token.get('token'))

        if self.ios_push_certificate_file and tokens_by_platform.get('iOS', []):
            try:
                self.send_ios_push_notifications(tokens_by_platform['iOS'], '{}: {}'.format(message['user']['username'], message['data']['text']))
            except Exception as error:
                import ipdb;ipdb.set_trace()
                exception_class = '{}.{}'.format(error.__class__.__module__, error.__class__.__name__)
                return_message = "iOS device push failed: {0}, reason: {1} {2}".format(tokens_by_platform['iOS'], exception_class, error.message)
                self.logger.info(return_message)
                raise BunnyMessageCancel()

        if self.android_push_api_key and tokens_by_platform.get('android', []):
            try:
                self.send_android_push_notifications(tokens_by_platform['android'], unpacked_message)
            except Exception as error:
                exception_class = '{}.{}'.format(error.__class__.__module__, error.__class__.__name__)
                return_message = "Android device push failed: {0}, reason: {1} {2}".format(tokens_by_platform['android'], exception_class, error.message)
                self.logger.info(return_message)
                raise BunnyMessageCancel()

        return

    def send_ios_push_notifications(self, tokens, message):
        con = self.ios_session.get_connection("push_production", cert_file=self.ios_push_certificate_file)
        message = Message(tokens, alert=message, badge=1, sound='default')

        # Send the message.
        srv = APNs(con)
        res = srv.send(message)

        # Check failures. Check codes in APNs reference docs.
        for token, reason in res.failed.items():
            code, errmsg = reason
            return_message = "[iOS] Device push failed: {0}, reason: {1}".format(token, errmsg)
            tokens.remove(token)
            self.logger.info(return_message)

        return_message = "[iOS] Successfully sent {} to {}.".format(message.alert, tokens)
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
