from maxbunny.utils import oauth2Header

import logging
import json
import requests

LOGGER = logging.getLogger('tweety')


def get_twitter_enabled_contexts(self):
    contexts = {}
    for max_settings in self.maxservers_settings:
        max_url = self.config.get(max_settings, 'server')
        req = requests.get('{}/contexts'.format(max_url), headers=oauth2Header(self.restricted_username, self.restricted_token))
        context_follow_list = [users_to_follow.get('twitterUsernameId') for users_to_follow in req.json().get('items') if users_to_follow.get('twitterUsernameId')]
        context_readable_follow_list = [users_to_follow.get('twitterUsername') for users_to_follow in req.json().get('items') if users_to_follow.get('twitterUsername')]
        contexts.setdefault(max_settings, {})['ids'] = context_follow_list
        contexts[max_settings]['readable'] = context_readable_follow_list

    return contexts, req


def get_followed_users_by_name(contexts):
    followed_users = {}
    for maxserver in contexts.keys():
        for username in contexts[maxserver].get('readable'):
            followed_users.setdefault(username, []).append(maxserver)
    return followed_users


def processTweetyMessage(self, message):
    message = json.loads(message)
    LOGGER.info(u"(INFO) Processing tweet {} from {} with content: {}".format(message.get('stid'), message.get('author'), message.get('message')))

    author = message.get('author').lower()

    contexts, req = get_twitter_enabled_contexts(self)
    followed_users = get_followed_users_by_name(contexts)

    import ipdb;ipdb.set_trace()
    # Check if the tweet is from a followed user
    # {'max_other': {'readable': [u'user1'], 'ids': [u'5674472']}, 'max_default': {'readable': [u'user1'], 'ids': [u'5674472']}}
    if author in followed_users:
        # Check if it's assigned to more than one MAX server
        if len(followed_users[author]) > 1:
            pass
        else:
            pass
