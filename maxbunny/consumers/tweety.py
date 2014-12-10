# -*- coding: utf-8 -*-
from maxbunny.consumer import BunnyMessageCancel
from maxbunny.consumer import BunnyConsumer
from maxbunny.utils import findHashtags
from maxcarrot.message import RabbitMessage

GENERATOR_ID = 'Twitter'

TWITTER_USER_NOT_LINKED_TO_MAX_USER = u'Discarding tweet {stid} from {author} : There\'s no MAX user with that twitter username.'
NO_SECONDARY_HASHTAGS_FOUND = u'tweet {stid} from {author} has only one (global) hashtag.'
NO_CONTEXT_FOUND_FOR_HASHTAGS = u'Discarding tweet {stid} from {author} with hashtags {hashtags} : There\'s no registered context with the supplied hashtags.'
MULTIPLE_CONTEXTS_MATCH_SAME_MAX = u'tweet {stid} from {author} eligible context found in more than one context in the max server "{maxserver}".'
MULTIPLE_CONTEXTS_MATCH_MULTIPLE_MAX = u'tweet {stid} from {author} eligible context found in more than one max server.'
MULTIPLE_GLOBAL_HASHTAGS_FOUND = u'tweet {stid} from {author} eligible context found in more than one max server. Tweet won\'t be posted to {maxservers}.'


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

        followed_users_per_max = self.get_followed_users_by_maxserver_name(self.contexts)

        # Check if the tweet is from a followed user
        if author in followed_users_per_max:
            # Check if it's assigned to more than one MAX server
            if len(followed_users_per_max[author]) > 1:
                self.logger.warning(MULTIPLE_CONTEXTS_MATCH_MULTIPLE_MAX.format(**twitter_message))

            contexts_assigned = self.get_contexts_by_followed_user(followed_users_per_max, author)

            contexts_found_per_max = {}
            for context in contexts_assigned:
                contexts_found_per_max.setdefault(context['maxserver'], 0)
                contexts_found_per_max[context['maxserver']] += 1

            for maxserver, context_count in contexts_found_per_max.items():
                # Check if it's assigned to more than one context inside each max
                if context_count > 1:
                    self.logger.warning(MULTIPLE_CONTEXTS_MATCH_SAME_MAX.format(maxserver=maxserver, **twitter_message))

            self.post_message_to_max_as_context(contexts_assigned, twitter_message)

        # We have a tweet from a tracked hashtag
        else:
            # Check if twitter_username is registered for a valid MAX username
            # if not, discard it
            if author not in self.get_registered_twitter_usernames_by_name(self.users):
                return_message = TWITTER_USER_NOT_LINKED_TO_MAX_USER.format(**twitter_message)
                raise BunnyMessageCancel(return_message, notify=False)

            # Parse text and separate global from context hashtags
            # ASSUMPTION:

            message_hashtags = findHashtags(twitter_message.get('message'))
            found_global_hashtags = []
            found_context_hashtags = []

            for hashtag in message_hashtags:
                if hashtag in self.global_hashtags:
                    found_global_hashtags.append(hashtag)
                else:
                    found_context_hashtags.append(hashtag)

            # ASSUMPTION:
            # If the message only contains global hashtags, then discard it
            # until further notice. In the future, it will be posted as a
            # 'timeline' message from the sender.
            if len(found_context_hashtags) == 0:
                return_message = NO_SECONDARY_HASHTAGS_FOUND.format(**twitter_message)
                raise BunnyMessageCancel(return_message)

            # If we don't have any global hashtag, this tweet is probably being processed
            # from a debug hashtag, and it will be found on found_context_hashtags
            # so log it and don't try to add it

            if len(found_global_hashtags) == 0:
                return_message = u"Discarding tweet {} from {} with unknown (probably debug) global hashtag found in [{}]".format(twitter_message.get('stid'), twitter_message.get('author'), ', '.join(found_context_hashtags))
                raise BunnyMessageCancel(return_message)

            # Alert of message not being published to multuple max servers
            if len(found_global_hashtags) > 1:
                self.logger.warning(MULTIPLE_GLOBAL_HASHTAGS_FOUND.format(maxservers=found_global_hashtags[1:], **twitter_message))

            # If we reached here, we have at least one global hashtag
            # For now we'll only use the first candidate found and discard others so
            # hashtag tweest to two different MAX servers simultaneously is not supported

            maxserver = self.global_hashtags[found_global_hashtags[0]]

            # Check if any hashtag is registered for a valid MAX context
            registered_hashtags = self.get_all_contexts_by_hashtag(self.contexts)
            context_hashtags = []
            for hashtag in found_context_hashtags:
                if hashtag in registered_hashtags:
                    context_hashtags.append(hashtag)

            context_assigned = self.get_contexts_by_hashtag(maxserver, context_hashtags)

            # Check if it's assigned to more than one context
            if len(context_assigned) > 1:
                self.logger.warning(MULTIPLE_CONTEXTS_MATCH_SAME_MAX.format(maxserver=maxserver, **twitter_message))

            # If we can't find anycontext registered for any of the message
            # hashtags, then discard it
            if len(context_assigned) == 0:
                return_message = NO_CONTEXT_FOUND_FOR_HASHTAGS.format(hashtags=unicode(found_context_hashtags), **twitter_message)
                raise BunnyMessageCancel(return_message)

            username = self.get_username_from_twitter_username(maxserver, author)
            self.post_message_to_max(context_assigned, username, twitter_message)

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

    def get_followed_users_by_maxserver_name(self, contexts):
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

    def get_contexts_by_followed_user(self, followed_users, author):
        eligible_contexts = []
        for maxserver in followed_users[author]:
            eligible_contexts = eligible_contexts + [self.add_maxserver(context, maxserver) for context in self.contexts[maxserver] if context.get('twitterUsername') == author]
        return eligible_contexts

    def get_contexts_by_hashtag(self, maxserver, hashtags):
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
