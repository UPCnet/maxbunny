from apnsclient import Message, APNs
from maxbunny.utils import oauth2Header

import json
import logging
import requests

LOGGER = logging.getLogger('push')


def processPushMessage(self, message):
    message = json.loads(message)
    conversation_id = message.get('conversation', None)
    if conversation_id is None:
        LOGGER.info('The message received is not a valid conversation')
        return

    req = requests.get('{}/conversations/{}/tokens'.format(self.config.get('max', 'server'), conversation_id),
                       headers=oauth2Header(self.restricted_username, self.restricted_token))
    tokens = req.json()

    itokens = []
    atokens = []
    for token in tokens.get('items'):
        # TODO: On production, not send notification to sender
        # if token.get('username') != message.get('username'):
        if token.get('platform') == 'iOS':
            itokens.append(token.get('token'))
        elif token.get('platform') == 'android':
            atokens.append(token.get('token'))

    send_ios_push_notifications(self, itokens, message.get('message'))
    send_android_push_notifications(self, atokens)


def send_ios_push_notifications(self, tokens, message):
    con = self.ios_session.get_connection("push_production",
                                          cert_file=self.config.get('push', 'push_certificate_file'))
    message = Message(tokens, alert=message, badge=1, sound='default')

    # Send the message.
    srv = APNs(con)
    res = srv.send(message)

    # Check failures. Check codes in APNs reference docs.
    for token, reason in res.failed.items():
        code, errmsg = reason
        LOGGER.info("Device push failed: {0}, reason: {1}".format(token, errmsg))

    LOGGER.info("Successfully sended {} to {}.".format(message.alert, tokens))


def send_android_push_notifications(self, tokens):
    pass
