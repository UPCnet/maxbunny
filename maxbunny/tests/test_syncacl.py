# -*- coding: utf-8 -*-
from maxbunny.consumer import BunnyMessageCancel

from maxbunny.tests import MockRunner
from maxbunny.tests import MaxBunnyTestCase
from maxbunny.tests import get_storing_logger
from maxbunny.tests import TEST_VHOST_URL

from maxbunny.tests.mock_http import http_mock_info
from maxbunny.tests.mock_http import http_mock_subscribe_user
from maxbunny.tests.mock_http import http_mock_grant_subscription_permission
from maxbunny.tests.mock_http import http_mock_revoke_subscription_permission

from maxcarrot import RabbitClient
from mock import patch
import httpretty


class SyncACLTests(MaxBunnyTestCase):
    def setUp(self):
        self.log_patch = patch('maxbunny.consumer.BunnyConsumer.configure_logger', new=get_storing_logger)
        self.log_patch.start()

    def tearDown(self):
        self.log_patch.stop()
        self.server.get_all('syncacl')
        self.server.disconnect()

        # Make sure httpretty is disabled
        httpretty.disable()
        httpretty.reset()

    def set_server(self, message, mid):
        self.server = RabbitClient(TEST_VHOST_URL)
        self.server.management.cleanup(delete_all=True)
        self.server.declare()

    # ==============================
    # TESTS FOR FAILING SCENARIOS
    # ==============================

    def test_message_missing_username(self):
        """

        """
        from maxbunny.consumers.syncacl import __consumer__
        from maxbunny.tests.mockers.syncacl import TASKS_MESSAGE_MISSING_USERNAME as message

        message_id = '00000000001'
        self.set_server(message, message_id)

        httpretty.enable()
        http_mock_info()

        runner = MockRunner('syncacl', 'maxbunny.ini', 'instances.ini')
        consumer = __consumer__(runner)

        self.assertRaisesWithMessage(
            BunnyMessageCancel,
            'Missing or empty user data',
            consumer.process,
            message
        )

        httpretty.disable()
        httpretty.reset()

    def test_message_missing_context(self):
        """

        """
        from maxbunny.consumers.syncacl import __consumer__
        from maxbunny.tests.mockers.syncacl import TASKS_MESSAGE_MISSING_CONTEXT as message

        message_id = '00000000001'
        self.set_server(message, message_id)

        httpretty.enable()
        http_mock_info()

        runner = MockRunner('syncacl', 'maxbunny.ini', 'instances.ini')
        consumer = __consumer__(runner)

        self.assertRaisesWithMessage(
            BunnyMessageCancel,
            'Missing or empty context url',
            consumer.process,
            message
        )

        httpretty.disable()
        httpretty.reset()

    def test_message_missing_tasks(self):
        """

        """
        from maxbunny.consumers.syncacl import __consumer__
        from maxbunny.tests.mockers.syncacl import TASKS_MESSAGE_MISSING_TASKS as message

        message_id = '00000000001'
        self.set_server(message, message_id)

        httpretty.enable()
        http_mock_info()

        runner = MockRunner('syncacl', 'maxbunny.ini', 'instances.ini')
        consumer = __consumer__(runner)

        self.assertRaisesWithMessage(
            BunnyMessageCancel,
            'Missing or empty tasks',
            consumer.process,
            message
        )

        httpretty.disable()
        httpretty.reset()

    # ==============================
    # TESTS FOR SUCCESFULL SCENARIOS
    # ==============================

    def test_message_with_tasks_all(self):
        """

        """
        from maxbunny.consumers.syncacl import __consumer__
        from maxbunny.tests.mockers.syncacl import TASKS_MESSAGE as message

        message_id = '00000000001'
        self.set_server(message, message_id)

        httpretty.enable()

        http_mock_info()
        http_mock_subscribe_user()
        http_mock_grant_subscription_permission()
        http_mock_revoke_subscription_permission()

        runner = MockRunner('syncacl', 'maxbunny.ini', 'instances.ini')
        consumer = __consumer__(runner)

        consumer.process(message)

        httpretty.disable()
        httpretty.reset()

        self.assertEqual(len(consumer.logger.infos), 1)

        self.assertTrue(consumer.logger.infos[0].startswith('[tests] SUCCEDED subscribe, -write, +read on e6847aed3105e85ae603c56eb2790ce85e212997 for testuser1'))

    def test_message_with_tasks_no_subscribe(self):
        """

        """
        from maxbunny.consumers.syncacl import __consumer__
        from maxbunny.tests.mockers.syncacl import TASKS_MESSAGE_NO_SUBSCRIBE as message

        message_id = '00000000001'
        self.set_server(message, message_id)

        httpretty.enable()

        http_mock_info()
        http_mock_subscribe_user()
        http_mock_grant_subscription_permission()
        http_mock_revoke_subscription_permission()

        runner = MockRunner('syncacl', 'maxbunny.ini', 'instances.ini')
        consumer = __consumer__(runner)

        consumer.process(message)

        httpretty.disable()
        httpretty.reset()

        self.assertEqual(len(consumer.logger.infos), 1)

        self.assertTrue(consumer.logger.infos[0].startswith('[tests] SUCCEDED -write, +read on e6847aed3105e85ae603c56eb2790ce85e212997 for testuser1'))
