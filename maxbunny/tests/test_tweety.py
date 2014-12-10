# -*- coding: utf-8 -*-
from maxbunny.consumer import BunnyMessageCancel
from maxbunny.consumers.tweety import TWITTER_USER_NOT_LINKED_TO_MAX_USER
from maxbunny.consumers.tweety import NO_SECONDARY_HASHTAGS_FOUND
from maxbunny.tests import MockRunner
from maxbunny.tests import MaxBunnyTestCase
from maxbunny.tests.mock_http import http_mock_info
from maxbunny.tests.mock_http import http_mock_contexts
from maxbunny.tests.mock_http import http_mock_users
from maxbunny.tests.mock_http import http_mock_post_context_activity
from maxbunny.tests.mock_http import http_mock_post_user_activity

import httpretty


class TweetyTests(MaxBunnyTestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @httpretty.activate
    def test_invalid_message(self):
        """
        """
        from maxbunny.consumers.tweety import __consumer__
        from maxbunny.tests.mockers import BAD_MESSAGE as message

        http_mock_info()

        runner = MockRunner('tweety', 'maxbunny.ini')
        consumer = __consumer__(runner)

        with self.assertRaises(BunnyMessageCancel):
            consumer.process(message)

        self.assertEqual(len(consumer.logger.infos), 0)
        self.assertEqual(len(consumer.logger.warnings), 0)

    @httpretty.activate
    def test_tweet_from_maxuser_to_context_max_empty(self):
        """
            Given there are no contexts linked with twitter_user
            And there are no users linked with twitter_user
            When a tweet from twitter_user is received without hashtags
            Then the tweet is not posted anywhere
            And the message is dropped with message TWITTER_USER_NOT_LINKED_TO_MAX_USER

        """
        from maxbunny.consumers.tweety import __consumer__
        from maxbunny.tests.mockers import TWEETY_MESSAGE_FROM_CONTEXT as message
        from maxbunny.tests.mockers import NO_CONTEXTS as contexts
        from maxbunny.tests.mockers import NO_USERS as users

        http_mock_info()
        http_mock_contexts(contexts)
        http_mock_users(users)

        runner = MockRunner('tweety', 'maxbunny.ini')
        consumer = __consumer__(runner)

        self.assertRaisesWithMessage(
            BunnyMessageCancel,
            TWITTER_USER_NOT_LINKED_TO_MAX_USER.format(**message['d']),
            consumer.process,
            message
        )

        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 0)

        self.assertTrue(consumer.logger.infos[0].startswith('Processing tweet'))

    @httpretty.activate
    def test_tweet_from_context_no_contexts(self):
        """
            Given there are no contexts linked with twitter_user
            And there is a user linked with twitter_user_context
            When a tweet from twitter_user_context is received without secondary hashtags
            Then the tweet is not posted anywhere
            And the tweet is matched as if it was a invalid hastag tweet
            And the message is dropped with message NO_SECONDARY_HASHTAGS_FOUND
        """
        from maxbunny.consumers.tweety import __consumer__
        from maxbunny.tests.mockers import TWEETY_MESSAGE_FROM_CONTEXT as message
        from maxbunny.tests.mockers import NO_CONTEXTS as contexts
        from maxbunny.tests.mockers import MIXED_USERS as users

        http_mock_info()
        http_mock_contexts(contexts)
        http_mock_users(users)

        runner = MockRunner('tweety', 'maxbunny.ini')
        consumer = __consumer__(runner)

        self.assertRaisesWithMessage(
            BunnyMessageCancel,
            NO_SECONDARY_HASHTAGS_FOUND.format(**message['d']),
            consumer.process,
            message
        )

        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 0)

        self.assertTrue(consumer.logger.infos[0].startswith('Processing tweet'))

    @httpretty.activate
    def test_tweet_from_context_succeed(self):
        """
            Given there is a context linked with twitter_context_user
            And there are no max users linked with twitter_context_user
            When a tweet from twitter_user is received
            Then the tweet is posted to the linked context
            And the processing is logged as succesfull
        """
        from maxbunny.consumers.tweety import __consumer__
        from maxbunny.tests.mockers import TWEETY_MESSAGE_FROM_CONTEXT as message
        from maxbunny.tests.mockers import SINGLE_CONTEXT as contexts
        from maxbunny.tests.mockers import SINGLE_USER as users

        http_mock_info()
        http_mock_contexts(contexts)
        http_mock_users(users)
        http_mock_post_context_activity()

        runner = MockRunner('tweety', 'maxbunny.ini')
        consumer = __consumer__(runner)
        consumer.process(message)

        self.assertEqual(len(consumer.logger.infos), 2)
        self.assertEqual(len(consumer.logger.warnings), 0)

        self.assertTrue(consumer.logger.infos[0].startswith('Processing tweet'))
        self.assertTrue(consumer.logger.infos[1].startswith('Successfully posted'))

    @httpretty.activate
    def test_tweet_from_maxuser_to_context_succeed(self):
        """
            Given there is a max user linked with twitter_user
            And a context linked to the #thehashtag
            When a tweet from twitter_user is received with #thehashtag
            Then the tweet is posted to the linked context
            And the processing is logged as succesfull
        """
        from maxbunny.consumers.tweety import __consumer__
        from maxbunny.tests.mockers import TWEETY_MESSAGE_FROM_USER as message
        from maxbunny.tests.mockers import SINGLE_CONTEXT as contexts
        from maxbunny.tests.mockers import SINGLE_USER as users

        http_mock_info()
        http_mock_contexts(contexts)
        http_mock_users(users)
        http_mock_post_user_activity()

        runner = MockRunner('tweety', 'maxbunny.ini')
        consumer = __consumer__(runner)
        consumer.process(message)

        self.assertEqual(len(consumer.logger.infos), 2)
        self.assertEqual(len(consumer.logger.warnings), 0)

        self.assertTrue(consumer.logger.infos[0].startswith('Processing tweet'))
        self.assertTrue(consumer.logger.infos[1].startswith('Successfully posted'))

    # @httpretty.activate
    # def test_tweet_with_invalid_hashtag(self):

    # @httpretty.activate
    # def test_tweet_with_only_a_global_hashtag(self):

    # @httpretty.activate
    # def test_tweet_with_hashtag_no_registered_user(self):
