# -*- coding: utf-8 -*-
from maxbunny.consumer import BunnyMessageCancel
from maxbunny.consumer import BunnyMessageRequeue

from maxbunny.tests import MockRunner
from maxbunny.tests import MockConnection
from maxbunny.tests import MockRabbitServer
from maxbunny.tests import MaxBunnyTestCase
from maxbunny.tests import get_storing_logger
from maxbunny.tests import is_rabbit_active
from maxbunny.tests import TEST_VHOST_URL
from maxbunny.tests.mock_http import http_mock_info
from maxbunny.tests.mock_http import http_mock_post_user_message

from maxbunny.tests.mockers.conversations import CONVERSATION_0

from maxcarrot import RabbitClient
from mock import patch
import httpretty
import warnings
from time import sleep

MOCK_RABBIT = not is_rabbit_active()
if MOCK_RABBIT:
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

        if MOCK_RABBIT:
            self.rabbit_patch = patch('rabbitpy.Connection', new=MockConnection)
            self.rabbit_patch.start()

    def tearDown(self):
        self.log_patch.stop()
        if MOCK_RABBIT:
            self.rabbit_patch.stop()
        else:
            if hasattr(self, 'server'):
                self.server.delete_user('testuser1')
                self.server.get_all('push')
                self.server.disconnect()

    def set_server(self, message, mid):
        if MOCK_RABBIT:
            self.server = MockRabbitServer(message, mid)
        else:
            self.server = RabbitClient(TEST_VHOST_URL)
            self.server.management.cleanup(delete_all=True)
            self.server.declare()
            self.server.create_users(CONVERSATION_0.users)
            self.server.conversations.create(CONVERSATION_0.id, users=CONVERSATION_0.users)

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

    def test_missing_domain_with_default(self):
        """
        """
        from maxbunny.consumers.conversations import __consumer__
        from maxbunny.tests.mockers.conversations import MISSING_DOMAIN_MESSAGE as message
        message_id = '00000000001'

        self.set_server(message, message_id)

        httpretty.enable()

        http_mock_info()
        http_mock_post_user_message(uri='tests.default', message_id=message_id)

        runner = MockRunner('tweety', 'maxbunny.ini', 'instances2.ini')
        consumer = __consumer__(runner)

        consumer.process(message)

        httpretty.disable()
        httpretty.reset()

        sleep(0.1)  # Leave a minimum time to message to reach rabbitmq
        messages = self.server.get_all('push')
        self.assertEqual(len(messages), 1)

        self.assertEqual(messages[0][0]['a'], 'k')
        self.assertEqual(messages[0][0]['o'], 'm')
        self.assertEqual(messages[0][0]['s'], 'b')
        self.assertEqual(messages[0][0]['d']['id'], '00000000001')
