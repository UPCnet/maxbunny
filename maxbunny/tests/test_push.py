# -*- coding: utf-8 -*-
from maxbunny.consumer import BunnyMessageCancel

from maxbunny.tests import MockRunner
from maxbunny.tests import MockAPNSSession
from maxbunny.tests import MockAPNs
from maxbunny.tests import set_apns_response
from maxbunny.tests import MaxBunnyTestCase
from maxbunny.tests import get_storing_logger
from maxbunny.tests.mock_http import http_mock_info
from maxbunny.tests.mock_http import http_mock_get_conversation_tokens

from mock import patch
import httpretty


class PushTests(MaxBunnyTestCase):
    def setUp(self):
        self.log_patch = patch('maxbunny.consumer.BunnyConsumer.configure_logger', new=get_storing_logger)
        self.log_patch.start()

        self.apns_server_patch = patch('apnsclient.APNs', new=MockAPNs)
        self.apns_server_patch.start()

        self.apns_session_patch = patch('apnsclient.Session', new=MockAPNSSession)
        self.apns_session_patch.start()

    def tearDown(self):
        self.log_patch.stop()
        self.apns_session_patch.stop()
        self.apns_session_patch.start()
        httpretty.disable()
        httpretty.reset()

    # ===========================
    # TESTS FOR FAILING SCENARIOS
    # ===========================

    @httpretty.activate
    def test_missing_push_service_keys(self):
        """
            Given there are no configured push keys
            When the message is processed
            Then an exception is raised
            And the push message is not sent
        """
        from maxbunny.consumers.push import __consumer__
        from maxbunny.tests.mockers import BAD_MESSAGE as message

        http_mock_info()

        runner = MockRunner('push', 'maxbunny.ini', 'instances.ini')
        consumer = __consumer__(runner)

        self.assertRaisesWithMessage(
            BunnyMessageCancel,
            'PUSH keys not configured',
            consumer.process,
            message
        )

        self.assertEqual(len(consumer.logger.infos), 0)
        self.assertEqual(len(consumer.logger.warnings), 0)

    @httpretty.activate
    def test_unknown_domain(self):
        """
            Given a message with an unknown domain
            When the message is processed
            Then an exception is raised
            And the push message is not sent
        """
        from maxbunny.consumers.push import __consumer__
        from maxbunny.tests.mockers.push import UNKNOWN_DOMAIN_CONVERSATION_ACK as message

        http_mock_info()

        runner = MockRunner('push', 'maxbunny.ini', 'instances.ini', 'cloudapis.ini')
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
    def test_missing_user(self):
        """
            Given a message with missing user field
            When the message is processed
            Then an exception is raised
            And the push message is not sent
        """
        from maxbunny.consumers.push import __consumer__
        from maxbunny.tests.mockers.push import MISSING_USER_CONVERSATION_ACK as message

        http_mock_info()

        runner = MockRunner('push', 'maxbunny.ini', 'instances.ini', 'cloudapis.ini')
        consumer = __consumer__(runner)

        self.assertRaisesWithMessage(
            BunnyMessageCancel,
            'Missing or empty user data',
            consumer.process,
            message
        )

        self.assertEqual(len(consumer.logger.infos), 0)
        self.assertEqual(len(consumer.logger.warnings), 0)

    @httpretty.activate
    def test_empty_user(self):
        """
            Given a message with empty username data
            When the message is processed
            Then an exception is raised
            And the push message is not sent
        """
        from maxbunny.consumers.push import __consumer__
        from maxbunny.tests.mockers.push import EMPTY_USER_CONVERSATION_ACK as message

        http_mock_info()

        runner = MockRunner('push', 'maxbunny.ini', 'instances.ini', 'cloudapis.ini')
        consumer = __consumer__(runner)

        self.assertRaisesWithMessage(
            BunnyMessageCancel,
            'Missing or empty user data',
            consumer.process,
            message
        )

        self.assertEqual(len(consumer.logger.infos), 0)
        self.assertEqual(len(consumer.logger.warnings), 0)

    @httpretty.activate
    def test_bad_message_routing_key(self):
        """
            Given a message with an routing_key
            And that routing_key doesn't match expected patterns
            When the message is processed
            Then an exception is raised
            And the push message is not sent
        """
        from maxbunny.consumers.push import __consumer__
        from maxbunny.tests.mockers.push import NOMATCH_ROUTING_KEY_CONVERSATION_ACK as message

        http_mock_info()

        runner = MockRunner('push', 'maxbunny.ini', 'instances.ini', 'cloudapis.ini')
        consumer = __consumer__(runner)

        self.assertRaisesWithMessage(
            BunnyMessageCancel,
            'The received message is not from a valid conversation',
            consumer.process,
            message
        )

        self.assertEqual(len(consumer.logger.infos), 0)
        self.assertEqual(len(consumer.logger.warnings), 0)

    @httpretty.activate
    def test_bad_message_id_on_routing_key(self):
        """
            Given a message with an routing_key
            And there is a bad identifier extracted from the key
            When the message is processed
            Then an exception is raised
            And the push message is not sent
        """
        from maxbunny.consumers.push import __consumer__
        from maxbunny.tests.mockers.push import NOID_ROUTING_KEY_CONVERSATION_ACK as message

        http_mock_info()

        runner = MockRunner('push', 'maxbunny.ini', 'instances.ini', 'cloudapis.ini')
        consumer = __consumer__(runner)

        self.assertRaisesWithMessage(
            BunnyMessageCancel,
            'The received message is not from a valid conversation',
            consumer.process,
            message
        )

        self.assertEqual(len(consumer.logger.infos), 0)
        self.assertEqual(len(consumer.logger.warnings), 0)

    @httpretty.activate
    def test_unknown_message_object_field(self):
        """
            Given a message with an unknown type on the object fied
            When the message is processed
            Then an exception is raised
            And the push message is not sent
        """
        from maxbunny.consumers.push import __consumer__
        from maxbunny.tests.mockers.push import UNKNOWN_OBJECT_CONVERSATION_ACK as message

        http_mock_info()

        runner = MockRunner('push', 'maxbunny.ini', 'instances.ini', 'cloudapis.ini')
        consumer = __consumer__(runner)

        self.assertRaisesWithMessage(
            BunnyMessageCancel,
            'The received message has an unknown object type',
            consumer.process,
            message
        )

        self.assertEqual(len(consumer.logger.infos), 0)
        self.assertEqual(len(consumer.logger.warnings), 0)

    @httpretty.activate
    def test_no_tokens(self):
        """
            Given a message with a ack from a testuser0 conversation message
            And users in conversation do not have tokens defined
            When the message is processed
            Then the push messages won't be sent
        """
        from maxbunny.consumers.push import __consumer__
        from maxbunny.tests.mockers.push import CONVERSATION_ACK as message

        http_mock_info()
        http_mock_get_conversation_tokens(tokens=[])

        runner = MockRunner('push', 'maxbunny.ini', 'instances.ini', 'cloudapis.ini')
        consumer = __consumer__(runner)

        self.assertRaisesWithMessage(
            BunnyMessageCancel,
            'No tokens received',
            consumer.process,
            message
        )

    @httpretty.activate
    def test_ios_push_apns_exception(self):
        """
            Given a message with a ack from a testuser0 conversation message
            And users in conversation do not have tokens defined
            When the message is processed
            Then the push messages won't be sent
        """
        from maxbunny.consumers.push import __consumer__
        from maxbunny.tests.mockers.push import CONVERSATION_ACK as message
        from maxbunny.tests.mockers.push import IOS_TOKENS as tokens

        http_mock_info()
        http_mock_get_conversation_tokens(tokens=tokens)

        runner = MockRunner('push', 'maxbunny.ini', 'instances.ini', 'cloudapis.ini')
        consumer = __consumer__(runner)
        set_apns_response(Exception('Push Service Crashed'))

        self.assertRaisesWithMessage(
            Exception,
            'Push Service Crashed',
            consumer.process,
            message
        )

    # ===============================
    # TESTS FOR SUCCESSFULL SCENARIOS
    # ===============================

    @httpretty.activate
    def test_ios_succeed(self):
        """
            Given a message with a ack from a testuser0 conversation message
            And users in conversation have valid device tokens
            When the message is processed
            Then the push message is sent
            And the sender don't receive the push
        """
        from maxbunny.consumers.push import __consumer__
        from maxbunny.tests.mockers.push import CONVERSATION_ACK as message
        from maxbunny.tests.mockers.push import IOS_TOKENS as tokens
        from maxbunny.tests.mockers.push import CONVERSATION_ACK_SUCCESS

        http_mock_info()
        http_mock_get_conversation_tokens(tokens=tokens)

        runner = MockRunner('push', 'maxbunny.ini', 'instances.ini', 'cloudapis.ini')
        consumer = __consumer__(runner)
        set_apns_response(CONVERSATION_ACK_SUCCESS)

        processed_tokens = consumer.process(message)

        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 0)

        self.assertEqual(consumer.logger.infos[0], '[tests] SUCCEDED 3/3 push messages.000000000000.000000000001 to testuser1,testuser2,testuser3')
        self.assertEqual(len(processed_tokens), 3)

    @httpretty.activate
    def test_ios_succeed_one_shared(self):
        """
            Given a message with a ack from a testuser0 conversation message
            And users in conversation have valid device tokens
            And testuser1 & testuser3 share the same token
            When the message is processed
            Then an exception is raised
            And the push message is sent
            And the device shared by testuser2 & testuser3 don't get the notification twice
            And the sender don't receive the push
        """
        from maxbunny.consumers.push import __consumer__
        from maxbunny.tests.mockers.push import CONVERSATION_ACK as message
        from maxbunny.tests.mockers.push import IOS_TOKENS_ONE_SHARED as tokens
        from maxbunny.tests.mockers.push import CONVERSATION_ACK_SUCCESS

        http_mock_info()
        http_mock_get_conversation_tokens(tokens=tokens)

        runner = MockRunner('push', 'maxbunny.ini', 'instances.ini', 'cloudapis.ini')
        consumer = __consumer__(runner)
        set_apns_response(CONVERSATION_ACK_SUCCESS)

        processed_tokens = consumer.process(message)

        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 1)

        self.assertEqual(consumer.logger.infos[0], '[tests] SUCCEDED 2/2 push messages.000000000000.000000000001 to testuser1,testuser2,testuser3')
        self.assertEqual(consumer.logger.warnings[0], '[tests] ios token 0123456789abcdef000000000000000000000000000000000000000000000002 shared by testuser2,testuser3')

        self.assertEqual(len(processed_tokens), 2)

    @httpretty.activate
    def test_ios_succeed_one_invalid(self):
        """
            Given a message with a ack from a testuser0 conversation message
            And users in conversation have valid device tokens
            And testuser3 has a invalid device token
            When the message is processed
            Then an exception is raised
            And the push message is sent
            And the sender don't receive the push
            And testuser3 don't receive the push
        """
        from maxbunny.consumers.push import __consumer__
        from maxbunny.tests.mockers.push import CONVERSATION_ACK as message
        from maxbunny.tests.mockers.push import IOS_TOKENS as tokens
        from maxbunny.tests.mockers.push import CONVERSATION_ACK_SUCCESS_ONE_INVALID

        http_mock_info()
        http_mock_get_conversation_tokens(tokens=tokens)

        runner = MockRunner('push', 'maxbunny.ini', 'instances.ini', 'cloudapis.ini')
        consumer = __consumer__(runner)
        set_apns_response(CONVERSATION_ACK_SUCCESS_ONE_INVALID)

        processed_tokens = consumer.process(message)

        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 1)

        self.assertEqual(consumer.logger.infos[0], '[tests] SUCCEDED 2/3 push messages.000000000000.000000000001 to testuser1,testuser2')
        self.assertEqual(consumer.logger.warnings[0], '[tests] FAILED ios push messages.000000000000.000000000001 to testuser3: ERR=8 Invalid Token')
        self.assertEqual(len(processed_tokens), 3)
