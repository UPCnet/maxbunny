# -*- coding: utf-8 -*-
from maxbunny.consumer import BunnyMessageCancel
from maxbunny.tests import MockRunner
from maxbunny.tests import MaxBunnyTestCase

import httpretty
import json
import re


def http_mock_info():
    httpretty.register_uri(
        httpretty.GET, "http://tests.local/info",
        body='{"max.oauth_server": "http://oauth.local"}',
        status=200,
        content_type="application/json"
    )


def http_mock_contexts(contexts):
    httpretty.register_uri(
        httpretty.GET, "http://tests.local/contexts?limit=0&twitter_enabled=True",
        body=json.dumps(contexts),
        status=200,
        content_type="application/json"
    )


def http_mock_users(users):
    httpretty.register_uri(
        httpretty.GET, "http://tests.local/people?limit=0&twitter_enabled=True",
        body=json.dumps(users),
        status=200,
        content_type="application/json"
    )


def http_mock_post_context_activity():
    httpretty.register_uri(
        httpretty.POST, re.compile("http://tests.local/contexts/\w+/activities"),
        body=json.dumps({}),
        status=200,
        content_type="application/json"
    )


def http_mock_post_user_activity():
    httpretty.register_uri(
        httpretty.POST, re.compile("http://tests.local/people/\w+/activities"),
        body=json.dumps({}),
        status=201,
        content_type="application/json"
    )


class TweetyTests(MaxBunnyTestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_invalid_message(self):
        """
        """
        from maxbunny.consumers.tweety import __consumer__
        from maxbunny.tests.mockers import BAD_MESSAGE as message

        runner = MockRunner('tweety', 'maxbunny.ini')
        consumer = __consumer__(runner)

        with self.assertRaises(BunnyMessageCancel):
            consumer.process(message)

    @httpretty.activate
    def test_tweet_from_maxuser_to_context_max_empty(self):
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
            "Discarding tweet 0 from twitter_user : There's no MAX user with that twitter username.",
            consumer.process,
            message
        )

    @httpretty.activate
    def test_tweet_from_maxuser_to_context_no_contexts(self):
        """
          Tweet from a followed twitter user (without hashtags), that
          won't go anywhere because  we didn't find the context it's related to.

          This scenario is matched as if it was a hashtag tweet, with missing second hashtag
        """
        from maxbunny.consumers.tweety import __consumer__
        from maxbunny.tests.mockers import TWEETY_MESSAGE_FROM_CONTEXT as message
        from maxbunny.tests.mockers import NO_CONTEXTS as contexts
        from maxbunny.tests.mockers import SINGLE_USER as users

        http_mock_info()
        http_mock_contexts(contexts)
        http_mock_users(users)

        runner = MockRunner('tweety', 'maxbunny.ini')
        consumer = __consumer__(runner)

        self.assertRaisesWithMessage(
            BunnyMessageCancel,
            "tweet 0 from twitter_user has only one (global) hashtag.",
            consumer.process,
            message
        )

    @httpretty.activate
    def test_tweet_from_context_succeed(self):
        """
          Tweet from a followed twitter user (without hashtags), that
          will be written to his related context.
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
          Tweet from a with a context hashtag, that will be written to his related context
          with author that is linked with its twitter username
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
