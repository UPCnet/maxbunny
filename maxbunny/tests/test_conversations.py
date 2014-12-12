# -*- coding: utf-8 -*-
from maxbunny.consumer import BunnyMessageCancel
from maxbunny.consumer import BunnyMessageRequeue

from maxbunny.tests import MockRunner
from maxbunny.tests import MockConnection
from maxbunny.tests import MaxBunnyTestCase
from maxbunny.tests import get_storing_logger
from maxbunny.tests import is_rabbit_active
from maxbunny.tests.mock_http import http_mock_info
from maxbunny.tests.mock_http import http_mock_post_user_message

from mock import patch
import httpretty
import warnings


if not is_rabbit_active():
    warnings.warn("""

        ************************ WARNING ********************

        Didn't found a running RabbitMQ Instance.
        All queue-related operations on tests will be mocked.

        *****************************************************
        """)


class ConversationTests(MaxBunnyTestCase):
    def setUp(self):
        self.log_patch = patch('maxbunny.consumer.BunnyConsumer.configure_logger', new=get_storing_logger)
        self.log_patch.start()

        if not is_rabbit_active():
            self.log_patch = patch('rabbitpy.Connection', new=MockConnection)
            self.log_patch.start()

    def tearDown(self):
        pass

    # ===========================
    # TESTS FOR FAILING SCENARIOS
    # ===========================

    @httpretty.activate
    def test_invalid_message_empty_message(self):
        """
        """
        from maxbunny.consumers.conversations import __consumer__
        from maxbunny.tests.mockers import BAD_MESSAGE as message

        http_mock_info()

        runner = MockRunner('tweety', 'maxbunny.ini', 'instances.ini')
        consumer = __consumer__(runner)

        self.assertRaisesWithMessage(
            BunnyMessageCancel,
            'Conversation id missing on routing_key ""',
            consumer.process,
            message
        )

        self.assertEqual(len(consumer.logger.infos), 0)
        self.assertEqual(len(consumer.logger.warnings), 0)

    @httpretty.activate
    def test_invalid_message_missing_username(self):
        """
        """
        from maxbunny.consumers.conversations import __consumer__
        from maxbunny.tests.mockers.conversations import MISSING_USERNAME_MESSAGE as message

        http_mock_info()

        runner = MockRunner('tweety', 'maxbunny.ini', 'instances2.ini')
        consumer = __consumer__(runner)

        self.assertRaisesWithMessage(
            BunnyMessageCancel,
            'Missing username in message',
            consumer.process,
            message
        )

        self.assertEqual(len(consumer.logger.infos), 0)
        self.assertEqual(len(consumer.logger.warnings), 0)

    @httpretty.activate
    def test_invalid_message_unknown_domain(self):
        """
        """
        from maxbunny.consumers.conversations import __consumer__
        from maxbunny.tests.mockers.conversations import UNKNOWN_DOMAIN_MESSAGE as message

        http_mock_info()

        runner = MockRunner('tweety', 'maxbunny.ini', 'instances2.ini')
        consumer = __consumer__(runner)

        self.assertRaisesWithMessage(
            BunnyMessageCancel,
            'Unknown domain "unknown"',
            consumer.process,
            message
        )

        self.assertEqual(len(consumer.logger.infos), 0)
        self.assertEqual(len(consumer.logger.warnings), 0)

    @httpretty.activate
    def test_missing_domain_missing_domain(self):
        """
        """
        from maxbunny.consumers.conversations import __consumer__
        from maxbunny.tests.mockers.conversations import MISSING_DOMAIN_MESSAGE as message

        http_mock_info()

        runner = MockRunner('tweety', 'maxbunny.ini', 'instances.ini')
        consumer = __consumer__(runner)

        self.assertRaisesWithMessage(
            BunnyMessageCancel,
            'Missing domain, and default could not be loaded',
            consumer.process,
            message
        )

        self.assertEqual(len(consumer.logger.infos), 0)
        self.assertEqual(len(consumer.logger.warnings), 0)

    @httpretty.activate
    def test_missing_domain_with_default(self):
        """
        """
        from maxbunny.consumers.conversations import __consumer__
        from maxbunny.tests.mockers.conversations import MISSING_DOMAIN_MESSAGE as message

        http_mock_info()
        http_mock_post_user_message(uri='tests.default')

        runner = MockRunner('tweety', 'maxbunny.ini', 'instances2.ini')
        consumer = __consumer__(runner)

        consumer.process(message)
        self.assertRaisesWithMessage(
            BunnyMessageCancel,
            ''.format(**message['d']),
            consumer.process,
            message
        )

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
