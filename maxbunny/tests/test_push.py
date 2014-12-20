# -*- coding: utf-8 -*-
from maxbunny.consumer import BunnyMessageCancel

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


class PushTests(MaxBunnyTestCase):
    def setUp(self):
        self.log_patch = patch('maxbunny.consumer.BunnyConsumer.configure_logger', new=get_storing_logger)
        self.log_patch.start()

    def tearDown(self):
        self.log_patch.stop()
        httpretty.disable()
        httpretty.reset()

    # ===========================
    # TESTS FOR FAILING SCENARIOS
    # ===========================

    @httpretty.activate
    def test_missing_push_service_keys(self):
        """
            Given there are no configured push  keys
            When the message is processed
            Then an exception is raised
            And the push message is not sent
        """
        from maxbunny.consumers.push import __consumer__
        from maxbunny.tests.mockers import BAD_MESSAGE as message

        http_mock_info()

        runner = MockRunner('tweety', 'maxbunny.ini', 'instances.ini')
        consumer = __consumer__(runner)

        self.assertRaisesWithMessage(
            BunnyMessageCancel,
            'PUSH keys not configured',
            consumer.process,
            message
        )

        self.assertEqual(len(consumer.logger.infos), 0)
        self.assertEqual(len(consumer.logger.warnings), 0)
