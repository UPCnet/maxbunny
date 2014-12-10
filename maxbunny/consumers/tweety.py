# -*- coding: utf-8 -*-
from maxbunny.consumer import BunnyMessageCancel
from maxbunny.consumer import BunnyConsumer
from maxbunny.utils import findHashtags
from maxcarrot.message import RabbitMessage

GENERATOR_ID = 'Twitter'

TWITTER_USER_NOT_LINKED_TO_MAX_USER = u"Discarding tweet {stid} from {author} : There's no MAX user with that twitter username."
NO_SECONDARY_HASHTAGS_FOUND = u"tweet {stid} from {author} has only one (global) hashtag."


class TweetyConsumer(BunnyConsumer):
    """
    """
    name = 'tweety'
    queue = 'twitter'
    logname = 'twitter-processor.log'

    def configure(self, runner):
        pass

    @property
    def contexts(self):
        return self.get_twitter_enabled_contexts()

    @property
    def users(self):
        return self.get_twitter_enabled_users()

    @property
    def global_hashtags(self):
        """
            Max each maxserver_id by it's configured global hashtag
        """
        return self.clients.client_ids_by_hashtag()

    def process(self, rabbitpy_message):
        """
        """
        message = RabbitMessage.unpack(rabbitpy_message.json())
        twitter_message = message.get('data', {})

        # Lowercased author to perform checks along the code
        author = twitter_message.get('author', None)
        if author is None:
            raise BunnyMessageCancel('Missing author field on tweet data')

        author = author.lower()

        self.logger.info(u"Processing tweet {stid} from {author} with content: {message}".format(**twitter_message))

        followed_users = self.get_followed_users_by_name(self.contexts)

        # Check if the tweet is from a followed user
        if author in followed_users:
            # Check if it's assigned to more than one MAX server
            if len(followed_users[author]) > 1:
                self.logger.warning(u"tweet {stid} from {author} eligible context found in more than one max server.".format(**twitter_message))

            context_assigned = self.get_context_by_follow_user(followed_users, author)

            # Check if it's assigned to more than one context
            if len(context_assigned) > 1:
                self.logger.warning(u"tweet {stid} from {author} eligible context found in more than one context in the same max server.".format(**twitter_message))

            self.post_message_to_max_as_context(context_assigned, twitter_message)

        # We have a tweet from a tracked hashtag
        else:
            # Check if twitter_username is registered for a valid MAX username
            # if not, discard it
            if author not in self.get_registered_twitter_usernames_by_name(self.users):
                return_message = TWITTER_USER_NOT_LINKED_TO_MAX_USER.format(**twitter_message)
                raise BunnyMessageCancel(return_message, notify=False)

            # Parse text and determine its corresponding MAX server
            # ASSUMPTION:
            # It only uses the first candidate found and discard others so using
            # two global hashtags will work only for one of them so routing a
            # tweet to two different MAX servers simultaneously is not supported
            maxserver = None
            message_hastags = findHashtags(twitter_message.get('message'))
            for hashtag in message_hastags:
                if hashtag in self.global_hashtags:
                    maxserver = self.global_hashtags[hashtag]
                    message_hastags.remove(hashtag)

            # ASSUMPTION:
            # If the message only contains a global hashtag, then discard it
            # until further notice. In the future, it will be posted as a
            # 'timeline' message from the sender.
            if len(message_hastags) == 0:
                return_message = NO_SECONDARY_HASHTAGS_FOUND.format(**twitter_message)
                raise BunnyMessageCancel(return_message)

            registered_hashtags = self.get_all_contexts_by_hashtag(self.contexts)

            # Check if any hashtag is registered for a valid MAX context
            context_hashtags = []
            for hashtag in message_hastags:
                if hashtag in registered_hashtags:
                    context_hashtags.append(hashtag)

            # If we don't have any maxserver defined here, probably we're processing a tweet
            # from a debug hashtag, so log it and don't try to add it
            if maxserver is not None:
                context_assigned = self.get_context_by_hashtag(maxserver, context_hashtags)

                # Check if it's assigned to more than one context
                if len(context_assigned) > 1:
                    self.logger.warning(u"tweet {stid} from {author} eligible context found in more than one context in the same max server.".format(**twitter_message))

                # If we can't find any registered hashtag for any of the message
                # hashtags, then discard it
                if len(context_assigned) == 0:
                    return_message = u"Discarding tweet {} from {} with hashtag {} : There's no registered context with the supplied hashtag.".format(twitter_message.get('stid'), twitter_message.get('author'), unicode(message_hastags))
                    raise BunnyMessageCancel(return_message)

                username = self.get_username_from_twitter_username(maxserver, author)
                self.post_message_to_max(context_assigned, username, twitter_message)
            else:
                return_message = u"Discarding tweet {} from {} with unknown (probably debug) global hashtag found in [{}]".format(twitter_message.get('stid'), twitter_message.get('author'), ', '.join(message_hastags))
                raise BunnyMessageCancel(return_message)

    def get_twitter_enabled_contexts(self):
        contexts = {}
        for server_id, client in self.clients.get_all():
            resp = client.contexts.get(qs={'twitter_enabled': True, 'limit': 0})
            contexts[server_id] = resp
        return contexts

    def get_twitter_enabled_users(self):
        users = {}
        for server_id, client in self.clients.get_all():
            resp = client.people.get(qs={'twitter_enabled': True, 'limit': 0})
            users[server_id] = resp
        return users

    def get_followed_users_by_name(self, contexts):
        followed_users = {}

        for maxserver in contexts.keys():
            for context in contexts[maxserver]:
                followed_users.setdefault(context.get('twitterUsername'), [])

                # In the case that the user key already contains a maxserver
                # add it only if it's not the same maxserver ...
                if maxserver not in followed_users[context.get('twitterUsername')]:
                    followed_users[context.get('twitterUsername')].append(maxserver)
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

    def get_context_by_follow_user(self, followed_users, author):
        eligible_contexts = []
        for maxserver in followed_users[author]:
            eligible_contexts = eligible_contexts + [self.add_maxserver(context, maxserver) for context in self.contexts[maxserver] if context.get('twitterUsername') == author]
        return eligible_contexts

    def get_context_by_hashtag(self, maxserver, hashtags):
        return [self.add_maxserver(context, maxserver) for context in self.contexts[maxserver] if context.get('twitterHashtag') in hashtags]

    def get_username_from_twitter_username(self, maxserver, twitter_username):
        for user in self.users[maxserver]:
            if user.get('twitterUsername') == twitter_username:
                return user.get('username')

    def post_message_to_max_as_context(self, context_assigned, message):
        """ Post message to the context of each MAX (ideally only one context in
            one MAX)
        """
        for context in context_assigned:
            endpoint = self.clients[context.get('maxserver')].contexts[context.get('url')].activities
            endpoint.post(object_content=message.get('message'), generator=GENERATOR_ID)
            self.logger.info(u"Successfully posted tweet {} from {} as context {}".format(message.get('stid'), message.get('author'), context.get('url')))

        return

    def post_message_to_max(self, context_assigned, username, message):
        """ Post message to the context of each MAX (ideally only one context in
            one MAX)
        """
        for context in context_assigned:
            endpoint = self.clients[context.get('maxserver')].people[username].activities
            endpoint.post(object_content=message.get('message'), contexts=[{'url': context.get('url'), 'objectType': 'context'}], generator=GENERATOR_ID)
            self.logger.info(u"Successfully posted tweet {} from {} to context {}".format(message.get('stid'), message.get('author'), context.get('url')))

        return

__consumer__ = TweetyConsumer
