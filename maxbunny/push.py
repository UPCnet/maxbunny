from apnsclient import Message, APNs

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

        success, code, response = self.bunny.maxclients[self.message.get('server_id')].pushtokens_by_conversation(self.message.get('conversation'))

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
            self.send_ios_push_notifications(itokens, self.message.get('message'))
            self.send_android_push_notifications(atokens)

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
            LOGGER.info(return_message)
            return return_message

        return_message = "Successfully sended {} to {}.".format(message.alert, tokens)
        LOGGER.info(return_message)
        return return_message

    def send_android_push_notifications(self, tokens):
        pass
