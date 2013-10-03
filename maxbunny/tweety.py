from maxbunny.utils import oauth2Header
from maxbunny.utils import findHashtags

import logging
import json
import requests

LOGGER = logging.getLogger('twitterprocessor')
GENERATOR_ID = 'Twitter'


class TweetyMessage(object):

    def __init__(self, bunny, message):
        self.bunny = bunny
        self.message = json.loads(message)
        self.author = self.message.get('author').lower()
        self.contexts = self.get_twitter_enabled_contexts()
        self.users = self.get_twitter_enabled_users()

        # Get a mapping for MAX server global hashtags
        self.global_hashtags = {}
        for maxserver in self.bunny.maxservers_settings:
            self.global_hashtags[self.bunny.instances.get(maxserver, 'hashtag')] = maxserver

    def get_twitter_enabled_contexts(self):
        contexts = {}
        for max_settings in self.bunny.maxservers_settings:
            max_url = self.bunny.instances.get(max_settings, 'server')
            max_username = self.bunny.instances.get(max_settings, 'restricted_user')
            max_token = self.bunny.instances.get(max_settings, 'restricted_user_token')
            req = requests.get('{}/contexts'.format(max_url), params={"twitter_enabled": True}, headers=oauth2Header(max_username, max_token))
            if req.status_code == 200:
                contexts[max_settings] = req.json()
        return contexts

    def get_twitter_enabled_users(self):
        users = {}
        for max_settings in self.bunny.maxservers_settings:
            max_url = self.bunny.instances.get(max_settings, 'server')
            max_username = self.bunny.instances.get(max_settings, 'restricted_user')
            max_token = self.bunny.instances.get(max_settings, 'restricted_user_token')
            req = requests.get('{}/people'.format(max_url), params={"twitter_enabled": True}, headers=oauth2Header(max_username, max_token))
            if req.status_code == 200:
                users[max_settings] = req.json()
        return users

    def get_followed_users_by_name(self, contexts):
        followed_users = {}
        for maxserver in contexts.keys():
            for context in contexts[maxserver]:
                followed_users.setdefault(context.get('twitterUsername'), []).append(maxserver)
        return followed_users

    def get_all_contexts_by_hashtag(self, contexts):
        hashtags = {}
        for maxserver in contexts.keys():
            for context in contexts[maxserver]:
                hashtags.setdefault(context.get('twitterHashtag'), []).append(maxserver)
        return hashtags

    def get_registered_twitter_usernames_by_name(self, users):
        registered_usernames = {}
        for maxserver in users.keys():
            for user in users[maxserver]:
                registered_usernames.setdefault(user.get('twitterUsername'), []).append(maxserver)
        return registered_usernames

    def add_maxserver(self, context, maxserver):
        context.update({'maxserver': maxserver})
        return context

    def get_context_by_follow_user(self, followed_users):
        eligible_contexts = []
        for maxserver in followed_users[self.author]:
            eligible_contexts = eligible_contexts + [self.add_maxserver(context, maxserver) for context in self.contexts[maxserver] if context.get('twitterUsername') == self.author]
        return eligible_contexts

    def get_context_by_hashtag(self, maxserver, hashtags):
        return [self.add_maxserver(context, maxserver) for context in self.contexts[maxserver] if context.get('twitterHashtag') in hashtags]

    def get_username_from_twitter_username(self, maxserver, twitter_username):
        for user in self.users[maxserver]:
            if user.get('twitterUsername') == twitter_username:
                return user.get('username')

    def post_message_to_max_as_context(self, context_assigned):
        """ Post message to the context of each MAX (ideally only one context in
            one MAX)
        """
        return_messages = []
        for context in context_assigned:
            success, code, response = self.bunny.maxclients[context.get('maxserver')].add_activity_as_context(self.message.get('message'), context.get('url'), generator=GENERATOR_ID)
            if code == 201:
                return_message = u"(201) Successfully posted tweet {} from {} as context {}".format(self.message.get('stid'), self.author, context.get('url'))
                return_messages.append(return_message)
                LOGGER.info(return_message)
            else:  # pragma: no cover
                return_message = u"({}) Error posting tweet as context {} of {} server - {}".format(code, context.get('url'), context.get('maxserver'), response)
                return_messages.append(return_message)
                LOGGER.error(return_message)

        return return_messages

    def post_message_to_max(self, context_assigned, username):
        """ Post message to the context of each MAX (ideally only one context in
            one MAX)
        """
        return_messages = []
        for context in context_assigned:
            success, code, response = self.bunny.maxclients[context.get('maxserver')].addActivity(self.message.get('message'), contexts=[context.get('url')], generator=GENERATOR_ID, username=username)
            if code == 201:
                return_message = u"(201) Successfully posted tweet {} from {} to context {}".format(self.message.get('stid'), self.author, context.get('url'))
                return_messages.append(return_message)
                LOGGER.info(return_message)
            else:  # pragma: no cover
                return_message = u"({}) Error posting tweet as user {} to context {} of server {} - {}".format(code, username, context.get('url'), context.get('maxserver'), response)
                return_messages.append(return_message)
                LOGGER.error(return_message)

        return return_messages

    def process(self):
        LOGGER.info(u"(INFO) Processing tweet {} from {} with content: {}".format(self.message.get('stid'), self.message.get('author'), self.message.get('message')))

        followed_users = self.get_followed_users_by_name(self.contexts)

        # Check if the tweet is from a followed user
        if self.author in followed_users:
            # Check if it's assigned to more than one MAX server
            if len(followed_users[self.author]) > 1:
                LOGGER.warning(u"(WARNING) tweet {} from {} eligible context found in more than one max server.".format(self.message.get('stid'), self.message.get('author')))

            context_assigned = self.get_context_by_follow_user(followed_users)

            # Check if it's assigned to more than one context
            if len(context_assigned) > 1:
                LOGGER.warning(u"(WARNING) tweet {} from {} eligible context found in more than one context in the same max server.".format(self.message.get('stid'), self.message.get('author')))

            return self.post_message_to_max_as_context(context_assigned)

        # We have a tweet from a tracked hashtag
        else:
            # Check if twitter_username is registered for a valid MAX username
            # if not, discard it
            if self.author not in self.get_registered_twitter_usernames_by_name(self.users):
                return_message = u"(404) Discarding tweet {} from {} : There's no MAX user with that twitter username.".format(self.message.get('stid'), self.author)
                LOGGER.info(return_message)
                return return_message

            # Parse text and determine its corresponding MAX server
            # ASSUMPTION:
            # It only uses the first candidate found and discard others so using
            # two global hashtags will work only for one of them so routing a
            # tweet to two different MAX servers simultaneously is not supported
            message_hastags = findHashtags(self.message.get('message'))
            for hashtag in message_hastags:
                if hashtag in self.global_hashtags:
                    maxserver = self.global_hashtags[hashtag]
                    message_hastags.remove(hashtag)

            # ASSUMPTION:
            # If the message only contains a global hashtag, then discard it
            # until further notice. In the future, it will be posted as a
            # 'timeline' message from the sender.
            if len(message_hastags) == 0:
                return_message = u"(501) tweet {} from {} has only one (global) hashtag.".format(self.message.get('stid'), self.message.get('author'))
                LOGGER.warning(return_message)
                return return_message

            registered_hashtags = self.get_all_contexts_by_hashtag(self.contexts)

            # Check if any hashtag is registered for a valid MAX context
            context_hashtags = []
            for hashtag in message_hastags:
                if hashtag in registered_hashtags:
                    context_hashtags.append(hashtag)

            context_assigned = self.get_context_by_hashtag(maxserver, context_hashtags)

            # Check if it's assigned to more than one context
            if len(context_assigned) > 1:
                LOGGER.warning(u"(WARNING) tweet {} from {} eligible context found in more than one context in the same max server.".format(self.message.get('stid'), self.message.get('author')))

            # If we can't find any registered hashtag for any of the message
            # hashtags, then discard it
            if len(context_assigned) == 0:
                return_message = u"(404) Discarding tweet {} from {} with hashtag {} : There's no registered context with the supplied hashtag.".format(self.message.get('stid'), self.author, unicode(message_hastags))
                LOGGER.info(return_message)
                return return_message

            username = self.get_username_from_twitter_username(maxserver, self.author)
            return self.post_message_to_max(context_assigned, username)
