from apnsclient import Message, APNs
from gcmclient import GCM, JSONMessage, GCMAuthenticationError

import json
import logging

LOGGER = logging.getLogger('push')


class PushMessage(object):

    def __init__(self, bunny, message):
        self.bunny = bunny
        self.message = json.loads(message)

    def process(self):
        conversation_id = self.message.get('conversation', None)
        if conversation_id is None:
            LOGGER.info('The message received is not a valid conversation')
            return

        success, code, response = self.bunny.maxclients['max_' + self.message.get('server_id')].pushtokens_by_conversation(self.message.get('conversation'))

        itokens = []
        atokens = []
        for token in response:
            # TODO: On production, not send notification to sender
            # if token.get('username') != self.message.get('username'):
            if token.get('platform') == 'iOS':
                itokens.append(token.get('token'))
            elif token.get('platform') == 'android':
                atokens.append(token.get('token'))

        if self.bunny.config.get('push', 'push_certificate_file'):
            try:
                self.send_ios_push_notifications(itokens, self.message.get('message'))
            except Exception, errmsg:
                return_message = "iOS device push failed: {0}, reason: {1}".format(itokens, errmsg)
                LOGGER.info(return_message)

        if self.bunny.config.get('push', 'android_push_api_key'):
            try:
                self.send_android_push_notifications(atokens, self.message.get('message'))
            except Exception, errmsg:
                return_message = "Android device push failed: {0}, reason: {1}".format(atokens, errmsg)
                LOGGER.info(return_message)

    def send_ios_push_notifications(self, tokens, message):
        con = self.bunny.ios_session.get_connection("push_production", cert_file=self.bunny.config.get('push', 'push_certificate_file'))
        message = Message(tokens, alert=message, badge=1, sound='default')

        # Send the message.
        srv = APNs(con)
        res = srv.send(message)

        # Check failures. Check codes in APNs reference docs.
        for token, reason in res.failed.items():
            code, errmsg = reason
            return_message = "Device push failed: {0}, reason: {1}".format(token, errmsg)
            tokens.remove(token)
            LOGGER.info(return_message)

        return_message = "Successfully sended {} to {}.".format(message.alert, tokens)
        LOGGER.info(return_message)
        return return_message

    def send_android_push_notifications(self, tokens):
        gcm = GCM(self.bunny.config.get('push', 'android_push_api_key'))

        # Construct (key => scalar) payload. do not use nested structures.
        data = {'str': 'string', 'int': 10}

        # Unicast or multicast message, read GCM manual about extra options.
        # It is probably a good idea to always use JSONMessage, even if you send
        # a notification to just 1 registration ID.
        # unicast = PlainTextMessage("registration_id", data, dry_run=True)
        multicast = JSONMessage(tokens, data, collapse_key='my.key', dry_run=True)

        try:
            # attempt send
            res_multicast = gcm.send(multicast)

            for res in [res_multicast]:
                # nothing to do on success
                for reg_id, msg_id in res.success.items():
                    LOGGER.info("Successfully sent %s as %s" % (reg_id, msg_id))

                # # update your registration ID's
                # for reg_id, new_reg_id in res.canonical.items():
                #     print "Replacing %s with %s in database" % (reg_id, new_reg_id)

                # probably app was uninstalled
                for reg_id in res.not_registered:
                    LOGGER.info("Invalid %s from database" % reg_id)

                # unrecoverably failed, these ID's will not be retried
                # consult GCM manual for all error codes
                for reg_id, err_code in res.failed.items():
                    LOGGER.info("Should remove %s because %s" % (reg_id, err_code))

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
            LOGGER.info("Your Google API key is rejected")
        except ValueError, e:
            # probably your extra options, such as time_to_live,
            # are invalid. Read error message for more info.
            LOGGER.info("Invalid message/option or invalid GCM response")
            print e.args[0]
        except Exception:
            # your network is down or maybe proxy settings
            # are broken. when problem is resolved, you can
            # retry the whole message.
            LOGGER.info("Something wrong with requests library")
