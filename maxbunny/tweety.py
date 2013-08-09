from maxbunny.utils import oauth2Header

import logging
import json
import requests

LOGGER = logging.getLogger('tweety')


class TweetyMessage(object):

    def __init__(self, bunny, message):
        self.bunny = bunny
        self.message = json.loads(message)
        self.author = self.message.get('author').lower()

    def get_twitter_enabled_contexts(self):
        contexts = {}
        for max_settings in self.bunny.maxservers_settings:
            max_url = self.bunny.config.get(max_settings, 'server')
            req = requests.get('{}/contexts'.format(max_url), headers=oauth2Header(self.bunny.restricted_username, self.bunny.restricted_token))
            contexts[max_settings] = req.json()
        return contexts

    def get_followed_users_by_name(self, contexts):
        followed_users = {}
        for maxserver in contexts.keys():
            for username in contexts[maxserver].get('twitterUsername'):
                followed_users.setdefault(username, []).append(maxserver)
        return followed_users

    def process(self):
        LOGGER.info(u"(INFO) Processing tweet {} from {} with content: {}".format(self.message.get('stid'), self.message.get('author'), self.message.get('message')))

        contexts = self.get_twitter_enabled_contexts()
        import ipdb;ipdb.set_trace()
        followed_users = self.get_followed_users_by_name(contexts)


        # Check if the tweet is from a followed user
        # {'max_other': {'readable': [u'user1'], 'ids': [u'5674472']}, 'max_default': {'readable': [u'user1'], 'ids': [u'5674472']}}
        if self.author in followed_users:
            # Check if it's assigned to more than one MAX server
            if len(followed_users[self.author]) > 1:
                pass
            else:
                pass

            context_follow_list = [users_to_follow.get('twitterUsernameId') for users_to_follow in req.json().get('items') if users_to_follow.get('twitterUsernameId')]
            context_readable_follow_list = [users_to_follow.get('twitterUsername') for users_to_follow in req.json().get('items') if users_to_follow.get('twitterUsername')]
            contexts.setdefault(max_settings, {})['ids'] = context_follow_list
            contexts[max_settings]['readable'] = context_readable_follow_list
