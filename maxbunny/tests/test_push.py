# -*- coding: utf-8 -*-
from maxbunny.consumer import BunnyMessageCancel

from maxbunny.tests import MockRunner
from maxbunny.tests import MockAPNSSession
from maxbunny.tests import MockAPNs
from maxbunny.tests import MockGCM
from maxbunny.tests import set_apns_response
from maxbunny.tests import set_gcm_response
from maxbunny.tests import MaxBunnyTestCase
from maxbunny.tests import get_storing_logger
from maxbunny.tests.mock_http import http_mock_info
from maxbunny.tests.mock_http import http_mock_get_conversation_tokens
from maxbunny.tests.mock_http import http_mock_get_context_tokens

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

        self.gcm_server_patch = patch('gcmclient.GCM', new=MockGCM)
        self.gcm_server_patch.start()

    def tearDown(self):
        self.log_patch.stop()
        self.apns_server_patch.stop()
        self.apns_session_patch.stop()
        self.gcm_server_patch.stop()
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
            And the apnsclient library raises an exception
            When the message is processed
            Then an exception is raised
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

    @httpretty.activate
    def test_android_push_apns_exception(self):
        """
            Given a message with a ack from a testuser0 conversation message
            And the gcmclient library raises an exception
            When the message is processed
            Then an exception is raised
        """
        from maxbunny.consumers.push import __consumer__
        from maxbunny.tests.mockers.push import CONVERSATION_ACK as message
        from maxbunny.tests.mockers.push import ANDROID_TOKENS as tokens

        http_mock_info()
        http_mock_get_conversation_tokens(tokens=tokens)

        runner = MockRunner('push', 'maxbunny.ini', 'instances.ini', 'cloudapis.ini')
        consumer = __consumer__(runner)
        set_gcm_response(Exception('Push Service Crashed'))

        self.assertRaisesWithMessage(
            Exception,
            'Push Service Crashed',
            consumer.process,
            message
        )

    @httpretty.activate
    def test_ios_succeed_all_invalid(self):
        """
            Given a message with a ack from a testuser0 conversation message
            And users in conversation have valid device tokens
            And testuser3 has a invalid device token
            When the message is processed
            Then anyone receives the push
        """
        from maxbunny.consumers.push import __consumer__
        from maxbunny.tests.mockers.push import CONVERSATION_ACK as message
        from maxbunny.tests.mockers.push import IOS_TOKENS as tokens
        from maxbunny.tests.mockers.push import CONVERSATION_ACK_SUCCESS_ALL_INVALID

        http_mock_info()
        http_mock_get_conversation_tokens(tokens=tokens)

        runner = MockRunner('push', 'maxbunny.ini', 'instances.ini', 'cloudapis.ini')
        consumer = __consumer__(runner)
        set_apns_response(CONVERSATION_ACK_SUCCESS_ALL_INVALID)

        processed_tokens = consumer.process(message)

        self.assertEqual(len(consumer.logger.infos), 0)
        self.assertEqual(len(consumer.logger.warnings), 3)

        self.assertEqual(consumer.logger.warnings[0], '[tests] FAILED ios push messages.000000000000.000000000001 to testuser1: ERR=8 Invalid Token')
        self.assertEqual(consumer.logger.warnings[1], '[tests] FAILED ios push messages.000000000000.000000000001 to testuser2: ERR=8 Invalid Token')
        self.assertEqual(consumer.logger.warnings[2], '[tests] FAILED ios push messages.000000000000.000000000001 to testuser3: ERR=8 Invalid Token')
        self.assertEqual(len(processed_tokens), 3)

    @httpretty.activate
    def test_android_succeed_all_failed_mixed(self):
        """
            Given a message with a ack from a testuser0 conversation message
            And users in conversation have valid device tokens
            And all users push make android push service to fail
            When the message is processed
            And the push message is sent
            And the sender don't receive the push
            Then anyone receives the push
        """
        from maxbunny.consumers.push import __consumer__
        from maxbunny.tests.mockers.push import CONVERSATION_ACK as message
        from maxbunny.tests.mockers.push import ANDROID_TOKENS as tokens
        from maxbunny.tests.mockers.push import ANDROID_ACK_SUCCESS_ALL_FAILED_MIXED as gcm_response

        http_mock_info()
        http_mock_get_conversation_tokens(tokens=tokens)

        runner = MockRunner('push', 'maxbunny.ini', 'instances.ini', 'cloudapis.ini')
        consumer = __consumer__(runner)
        set_gcm_response(gcm_response)

        processed_tokens = consumer.process(message)

        self.assertEqual(len(consumer.logger.infos), 0)
        self.assertEqual(len(consumer.logger.warnings), 3)

        self.assertEqual(consumer.logger.warnings[0], '[tests] FAILED android push messages.000000000000.000000000001 to testuser1: Unavailable')
        self.assertEqual(consumer.logger.warnings[1], '[tests] FAILED android push messages.000000000000.000000000001 to testuser2: Not Registered')
        self.assertEqual(consumer.logger.warnings[2], '[tests] FAILED android push messages.000000000000.000000000001 to testuser3: Android error message')
        self.assertEqual(len(processed_tokens), 3)

    @httpretty.activate
    def test_ios_failed_conversation_creation_ack(self):
        """
            Given a message with a ack from a testuser0 conversation creation
            And the conversation id is missing
            And users in conversation have valid device tokens
            When the message is processed
            Then an exception is raised
            And the push message is not sent
        """
        from maxbunny.consumers.push import __consumer__
        from maxbunny.tests.mockers.push import BAD_ID_CONVERSATION_CREATION_ACK as message
        from maxbunny.tests.mockers.push import IOS_TOKENS as tokens

        http_mock_info()
        http_mock_get_conversation_tokens(tokens=tokens)

        runner = MockRunner('push', 'maxbunny.ini', 'instances.ini', 'cloudapis.ini')
        consumer = __consumer__(runner)

        self.assertRaisesWithMessage(
            BunnyMessageCancel,
            'The received message is not from a valid conversation',
            consumer.process,
            message
        )

    @httpretty.activate
    def test_ios_failed_activity_creation_ack(self):
        """
            Given a message with a ack from a testuser0 post to a context
            And the context id is missing
            And users in conversation have valid device tokens
            When the message is processed
            Then the push message is sent
            And the sender don't receive the push
        """
        from maxbunny.consumers.push import __consumer__
        from maxbunny.tests.mockers.push import BAD_ID_ACTIVITY_ACK as message
        from maxbunny.tests.mockers.push import IOS_TOKENS as tokens

        http_mock_info()
        http_mock_get_context_tokens(tokens=tokens)

        runner = MockRunner('push', 'maxbunny.ini', 'instances.ini', 'cloudapis.ini')
        consumer = __consumer__(runner)

        self.assertRaisesWithMessage(
            BunnyMessageCancel,
            'The received message is not from a valid context',
            consumer.process,
            message
        )

    # ===============================
    # TESTS FOR SUCCESSFULL SCENARIOS
    # ===============================

    @httpretty.activate
    def test_ios_pushdebug(self):
        """
            Given a message with a ack from a testuser0 conversation message
            And the message has the #pushdebug hashtag
            And users in conversation have valid device tokens
            When the message is processed
            Then the push message is sent
            And the sender don't receive the push
        """
        from maxbunny.consumers.push import __consumer__
        from maxbunny.tests.mockers.push import CONVERSATION_PUSHDEBUG_ACK as message
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

        self.assertEqual(consumer.logger.infos[0], '[tests] SUCCEDED 4/4 push messages.000000000000.000000000001 to testuser0,testuser1,testuser2,testuser3')
        self.assertEqual(len(processed_tokens), 4)

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

    @httpretty.activate
    def test_android_succeed(self):
        """
            Given a message with a ack from a testuser0 conversation message
            And users in conversation have valid device tokens
            When the message is processed
            Then the push message is sent
            And the sender don't receive the push
        """
        from maxbunny.consumers.push import __consumer__
        from maxbunny.tests.mockers.push import CONVERSATION_ACK as message
        from maxbunny.tests.mockers.push import ANDROID_TOKENS as tokens
        from maxbunny.tests.mockers.push import ANDROID_ACK_SUCCESS as gcm_response

        http_mock_info()
        http_mock_get_conversation_tokens(tokens=tokens)

        runner = MockRunner('push', 'maxbunny.ini', 'instances.ini', 'cloudapis.ini')
        consumer = __consumer__(runner)
        set_gcm_response(gcm_response)

        processed_tokens = consumer.process(message)

        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 0)

        self.assertEqual(consumer.logger.infos[0], '[tests] SUCCEDED 3/3 push messages.000000000000.000000000001 to testuser1,testuser2,testuser3')
        self.assertEqual(len(processed_tokens), 3)

    @httpretty.activate
    def test_android_succeed_one_failed(self):
        """
            Given a message with a ack from a testuser0 conversation message
            And users in conversation have valid device tokens
            And testuser3 make android push service to fail
            When the message is processed
            And the push message is sent
            And the sender don't receive the push
            And testuser3 don't receive the push
        """
        from maxbunny.consumers.push import __consumer__
        from maxbunny.tests.mockers.push import CONVERSATION_ACK as message
        from maxbunny.tests.mockers.push import ANDROID_TOKENS as tokens
        from maxbunny.tests.mockers.push import ANDROID_ACK_SUCCESS_ONE_FAILED as gcm_response

        http_mock_info()
        http_mock_get_conversation_tokens(tokens=tokens)

        runner = MockRunner('push', 'maxbunny.ini', 'instances.ini', 'cloudapis.ini')
        consumer = __consumer__(runner)
        set_gcm_response(gcm_response)

        processed_tokens = consumer.process(message)

        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 1)

        self.assertEqual(consumer.logger.infos[0], '[tests] SUCCEDED 2/3 push messages.000000000000.000000000001 to testuser1,testuser2')
        self.assertEqual(consumer.logger.warnings[0], '[tests] FAILED android push messages.000000000000.000000000001 to testuser3: Android error message')
        self.assertEqual(len(processed_tokens), 3)

    @httpretty.activate
    def test_android_ios_mixed_succeed(self):
        """
            Given a message with a ack from a testuser0 conversation message
            And users in conversation have valid device tokens
            And there are tokens from both ios and android
            When the message is processed
            And the push message is sent
            And the sender don't receive the push

        """
        from maxbunny.consumers.push import __consumer__
        from maxbunny.tests.mockers.push import CONVERSATION_ACK as message
        from maxbunny.tests.mockers.push import IOS_TOKENS
        from maxbunny.tests.mockers.push import ANDROID_TOKENS
        from maxbunny.tests.mockers.push import ANDROID_ACK_SUCCESS as gcm_response
        from maxbunny.tests.mockers.push import CONVERSATION_ACK_SUCCESS as apns_response

        http_mock_info()
        http_mock_get_conversation_tokens(tokens=IOS_TOKENS + ANDROID_TOKENS)

        runner = MockRunner('push', 'maxbunny.ini', 'instances.ini', 'cloudapis.ini')
        consumer = __consumer__(runner)
        set_gcm_response(gcm_response)
        set_apns_response(apns_response)

        processed_tokens = consumer.process(message)

        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 0)

        self.assertEqual(consumer.logger.infos[0], '[tests] SUCCEDED 6/6 push messages.000000000000.000000000001 to testuser1,testuser2,testuser3')
        self.assertEqual(len(processed_tokens), 6)

    @httpretty.activate
    def test_ios_succeed_conversation_creation(self):
        """
            Given a message with a ack from a testuser0 conversation creation
            And users in conversation have valid device tokens
            When the message is processed
            Then the push message is sent
            And the sender don't receive the push
        """
        from maxbunny.consumers.push import __consumer__
        from maxbunny.tests.mockers.push import CONVERSATION_CREATION_ACK as message
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
    def test_ios_succeed_activity_creation(self):
        """
            Given a message with a ack from a testuser0 post to a context
            And users in conversation have valid device tokens
            When the message is processed
            Then the push message is sent
            And the sender don't receive the push
        """
        from maxbunny.consumers.push import __consumer__
        from maxbunny.tests.mockers.push import ACTIVITY_ACK as message
        from maxbunny.tests.mockers.push import IOS_TOKENS as tokens
        from maxbunny.tests.mockers.push import CONVERSATION_ACK_SUCCESS

        http_mock_info()
        http_mock_get_context_tokens(tokens=tokens)

        runner = MockRunner('push', 'maxbunny.ini', 'instances.ini', 'cloudapis.ini')
        consumer = __consumer__(runner)
        set_apns_response(CONVERSATION_ACK_SUCCESS)

        processed_tokens = consumer.process(message)

        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 0)

        self.assertEqual(consumer.logger.infos[0], '[tests] SUCCEDED 3/3 push activity.000000000000.000000000001 to testuser1,testuser2,testuser3')
        self.assertEqual(len(processed_tokens), 3)
