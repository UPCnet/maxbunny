# -*- coding: utf-8 -*-
from maxbunny.consumer import BunnyMessageCancel
from maxbunny.consumer import BunnyMessageRequeue

from maxbunny.tests import MockRunner
from maxbunny.tests import MaxBunnyTestCase
from maxbunny.tests.mock_http import http_mock_info
from maxbunny.tests.mock_http import http_mock_contexts
from maxbunny.tests.mock_http import http_mock_users

import httpretty


class ConversationTests(MaxBunnyTestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    # ===========================
    # TESTS FOR FAILING SCENARIOS
    # ===========================

    @httpretty.activate
    def test_invalid_message(self):
        """
        """
        from maxbunny.consumers.conversations import __consumer__
        from maxbunny.tests.mockers import BAD_MESSAGE as message

        http_mock_info()

        runner = MockRunner('tweety', 'maxbunny.ini')
        consumer = __consumer__(runner)

        with self.assertRaises(BunnyMessageCancel):
            consumer.process(message)

        self.assertEqual(len(consumer.logger.infos), 0)
        self.assertEqual(len(consumer.logger.warnings), 0)

    # @httpretty.activate
    # def test_tweet_from_followed_user_max_empty(self):
    #     """
    #         Given there are no contexts linked with @twitter_user
    #         And there are no users followed with @twitter_user
    #         When a tweet from @twitter_user is received without hashtags
    #         Then the tweet is not posted anywhere
    #         And the message is dropped with message TWITTER_USER_NOT_LINKED_TO_MAX_USER

    #     """
    #     from maxbunny.consumers.tweety import __consumer__
    #     from maxbunny.tests.mockers import TWEETY_MESSAGE_FROM_CONTEXT as message
    #     from maxbunny.tests.mockers import NO_CONTEXTS as contexts
    #     from maxbunny.tests.mockers import NO_USERS as users

    #     http_mock_info()
    #     http_mock_contexts(contexts)
    #     http_mock_users(users)

    #     runner = MockRunner('tweety', 'maxbunny.ini')
    #     consumer = __consumer__(runner)

    #     self.assertRaisesWithMessage(
    #         BunnyMessageCancel,
    #         TWITTER_USER_NOT_LINKED_TO_MAX_USER.format(**message['d']),
    #         consumer.process,
    #         message
    #     )

    #     self.assertEqual(len(consumer.logger.infos), 1)
    #     self.assertEqual(len(consumer.logger.warnings), 0)

    #     self.assertTrue(consumer.logger.infos[0].startswith('Processing tweet'))
