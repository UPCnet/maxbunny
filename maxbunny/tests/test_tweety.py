# -*- coding: utf-8 -*-
from maxbunny.consumer import BunnyMessageCancel
from maxbunny.consumers.tweety import TWITTER_USER_NOT_LINKED_TO_MAX_USER
from maxbunny.consumers.tweety import NO_SECONDARY_HASHTAGS_FOUND
from maxbunny.consumers.tweety import NO_CONTEXT_FOUND_FOR_HASHTAGS
from maxbunny.consumers.tweety import MULTIPLE_CONTEXTS_MATCH_SAME_MAX
from maxbunny.consumers.tweety import MULTIPLE_CONTEXTS_MATCH_MULTIPLE_MAX
from maxbunny.consumers.tweety import MULTIPLE_GLOBAL_HASHTAGS_FOUND

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

    # ===========================
    # TESTS FOR FAILING SCENARIOS
    # ===========================

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
    def test_tweet_from_followed_user_max_empty(self):
        """
            Given there are no contexts linked with twitter_user
            And there are no users followed with twitter_user
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
    def test_hashtag_tweet_user_max_empty(self):
        """
            Given there are no contexts linked with twitter_user
            And there are no users followed with twitter_user
            When a hashtag tweet from twitter_user is received
            Then the tweet is not posted anywhere
            And the message is dropped with message TWITTER_USER_NOT_LINKED_TO_MAX_USER

        """
        from maxbunny.consumers.tweety import __consumer__
        from maxbunny.tests.mockers import TWEETY_MESSAGE_FROM_USER as message
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
    def test_hashtag_tweet_no_context_found(self):
        """
            Given there are no contexts linked with twitter_user
            And there is a user liked to twitter_user
            When a hashtag tweet from twitter_user is received
            Then the tweet is not posted anywhere
            And the message is dropped with message NO_CONTEXT_FOUND_FOR_HASHTAGS
        """
        from maxbunny.consumers.tweety import __consumer__
        from maxbunny.tests.mockers import TWEETY_MESSAGE_FROM_USER as message
        from maxbunny.tests.mockers import NO_CONTEXTS as contexts
        from maxbunny.tests.mockers import SINGLE_USER as users

        http_mock_info()
        http_mock_contexts(contexts)
        http_mock_users(users)

        runner = MockRunner('tweety', 'maxbunny.ini')
        consumer = __consumer__(runner)

        self.assertRaisesWithMessage(
            BunnyMessageCancel,
            NO_CONTEXT_FOUND_FOR_HASHTAGS.format(hashtags=['thehashtag'], **message['d']),
            consumer.process,
            message
        )

        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 0)

        self.assertTrue(consumer.logger.infos[0].startswith('Processing tweet'))

    @httpretty.activate
    def test_hashtag_tweet_from_folowed_user_no_contexts(self):
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

    # ===================================================
    # TESTS FOR SUCCESSFULL SCENARIOS, SINGLE DESTINATION
    # ===================================================

    @httpretty.activate
    def test_tweet_from_followed_user_succeed(self):
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
    def test_hashtag_tweet_from_maxuser_to_context_succeed(self):
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

    @httpretty.activate
    def test_tweet_from_followed_mixed_with_hashtag_user_succeed(self):
        """
            Given there is a context linked with twitter_user
            And there is another context linked to #thehastag
            And there is a max user linked with twitter_user
            When a tweet from twitter_user is received with #thehashtag
            Then the followed user scenario takes precedence
            And the tweet is posted only the the followed user context
            And the processing is logged as succesfull
        """
        from maxbunny.consumers.tweety import __consumer__
        from maxbunny.tests.mockers import TWEETY_MESSAGE_FROM_USER as message
        from maxbunny.tests.mockers import TWO_MIXED_CONTEXTS as contexts
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
        self.assertIn(contexts[1]['url'], consumer.logger.infos[1])

    # =================================================================
    # TESTS FOR SUCCESSFULL SCENARIOS, MULTIPLE DESTINATION ON SAME MAX
    # =================================================================

    @httpretty.activate
    def test_tweet_from_followed_user_to_multiple_contexts_same_followed_user_succeed(self):
        """
            Given there is more than one context linked with twitter_context_user
            And there are no max users linked with twitter_context_user
            When a tweet from twitter_context_user is received
            Then the tweet is posted to all linked contexts
            And the processing is logged as succesfull
        """
        from maxbunny.consumers.tweety import __consumer__
        from maxbunny.tests.mockers import TWEETY_MESSAGE_FROM_CONTEXT as message
        from maxbunny.tests.mockers import SHARED_INFO_CONTEXTS as contexts
        from maxbunny.tests.mockers import SINGLE_USER as users

        http_mock_info()
        http_mock_contexts(contexts)
        http_mock_users(users)
        http_mock_post_context_activity()

        runner = MockRunner('tweety', 'maxbunny.ini')
        consumer = __consumer__(runner)
        consumer.process(message)

        self.assertEqual(len(consumer.logger.infos), 3)
        self.assertEqual(len(consumer.logger.warnings), 1)

        self.assertTrue(consumer.logger.infos[0].startswith('Processing tweet'))
        self.assertTrue(consumer.logger.infos[1].startswith('Successfully posted'))
        self.assertTrue(consumer.logger.infos[2].startswith('Successfully posted'))

        self.assertEqual(consumer.logger.warnings[0], MULTIPLE_CONTEXTS_MATCH_SAME_MAX.format(maxserver='tests', **message['d']))

    @httpretty.activate
    def test_hashtag_tweet_to_multiple_contexts_same_hashtag_succeed(self):
        """
            Given there is a max user linked with twitter_user
            And multiple contexts linked to the #thehashtag
            When a tweet from twitter_user is received with #thehashtag
            Then the tweet is posted to all the linked contexts
            And the processing is logged as succesfull
        """
        from maxbunny.consumers.tweety import __consumer__
        from maxbunny.tests.mockers import TWEETY_MESSAGE_FROM_USER as message
        from maxbunny.tests.mockers import SHARED_INFO_CONTEXTS as contexts
        from maxbunny.tests.mockers import SINGLE_USER as users

        http_mock_info()
        http_mock_contexts(contexts)
        http_mock_users(users)
        http_mock_post_user_activity()

        runner = MockRunner('tweety', 'maxbunny.ini')
        consumer = __consumer__(runner)
        consumer.process(message)

        self.assertEqual(len(consumer.logger.infos), 3)
        self.assertEqual(len(consumer.logger.warnings), 1)

        self.assertTrue(consumer.logger.infos[0].startswith('Processing tweet'))
        self.assertTrue(consumer.logger.infos[1].startswith('Successfully posted'))
        self.assertTrue(consumer.logger.infos[1].startswith('Successfully posted'))

        self.assertEqual(consumer.logger.warnings[0], MULTIPLE_CONTEXTS_MATCH_SAME_MAX.format(maxserver='tests', **message['d']))

    @httpretty.activate
    def test_hashtag_tweet_to_multiple_contexts_different_hashtags_succeed(self):
        """
            Given there is a max user linked with twitter_user
            And a context linked to #thehashtag
            And a seconds context linked to #theotherhashtag
            When a tweet from twitter_user is received with both thehashtag and #theotherhashtag
            Then the tweet is posted to all the linked contexts
            And the processing is logged as succesfull
        """
        from maxbunny.consumers.tweety import __consumer__
        from maxbunny.tests.mockers import TWEETY_MESSAGE_FROM_USER_TWO_SECONDARY_HASHTAGS as message
        from maxbunny.tests.mockers import TWO_HASHTAG_CONTEXTS as contexts
        from maxbunny.tests.mockers import SINGLE_USER as users

        http_mock_info()
        http_mock_contexts(contexts)
        http_mock_users(users)
        http_mock_post_user_activity()

        runner = MockRunner('tweety', 'maxbunny.ini')
        consumer = __consumer__(runner)
        consumer.process(message)

        self.assertEqual(len(consumer.logger.infos), 3)
        self.assertEqual(len(consumer.logger.warnings), 1)

        self.assertTrue(consumer.logger.infos[0].startswith('Processing tweet'))
        self.assertTrue(consumer.logger.infos[1].startswith('Successfully posted'))
        self.assertTrue(consumer.logger.infos[1].startswith('Successfully posted'))

        self.assertEqual(consumer.logger.warnings[0], MULTIPLE_CONTEXTS_MATCH_SAME_MAX.format(maxserver='tests', **message['d']))

    # ========================================================================
    # TESTS FOR SUCCESSFULL SCENARIOS, MULTIPLE DESTINATION ON DIFFERENT MAX'S
    # ========================================================================

    @httpretty.activate
    def test_tweet_from_followed_user_to_multiple_contexts_same_followed_user_in_different_max_succeed(self):
        """
            Given there is more than one context linked with twitter_context_user
            And those contexts are located in different max instances
            And there are no max users linked with twitter_context_user in any of the max instances
            When a tweet from twitter_context_user is received
            Then the tweet is posted to all matched contexts across all matched max instances
            And the processing is logged as succesfull
        """
        from maxbunny.consumers.tweety import __consumer__
        from maxbunny.tests.mockers import TWEETY_MESSAGE_FROM_CONTEXT as message
        from maxbunny.tests.mockers import CONTEXTS_SHARED_MAX_1 as contexts1
        from maxbunny.tests.mockers import CONTEXTS_SHARED_MAX_2 as contexts2
        from maxbunny.tests.mockers import SINGLE_USER as users

        http_mock_info()

        http_mock_users(users)
        http_mock_contexts(contexts1)
        http_mock_post_context_activity()

        http_mock_users(users, uri='tests.local2')
        http_mock_contexts(contexts2, uri='tests.local2')
        http_mock_post_context_activity(uri='tests.local2')

        runner = MockRunner('tweety', 'maxbunny.ini', count=2)
        consumer = __consumer__(runner)
        consumer.process(message)

        self.assertEqual(len(consumer.logger.infos), 3)
        self.assertEqual(len(consumer.logger.warnings), 1)

        self.assertTrue(consumer.logger.infos[0].startswith('Processing tweet'))
        self.assertTrue(consumer.logger.infos[1].startswith('Successfully posted'))
        self.assertTrue(consumer.logger.infos[2].startswith('Successfully posted'))

        self.assertIn(contexts1[0]['url'], consumer.logger.infos[2])
        self.assertIn(contexts2[0]['url'], consumer.logger.infos[1])

        self.assertEqual(consumer.logger.warnings[0], MULTIPLE_CONTEXTS_MATCH_MULTIPLE_MAX.format(**message['d']))

    @httpretty.activate
    def test_hashtag_tweet_to_multiple_contexts_same_hashtag_in_different_max_succeed(self):
        """
            Given there is more than one context linked with #thehashtag
            And there are users linked with twitter_user
            And those contexts and users are located in different max instances
            And those max instances has different global hashtags

            When a tweet from twitter_user is received with #thehashtag
            ???
            Then the tweet is posted to all linked contexts
            And the processing is logged as succesfull
        """
        from maxbunny.consumers.tweety import __consumer__
        from maxbunny.tests.mockers import TWEETY_MESSAGE_FROM_USER_TWO_GLOBAL as message
        from maxbunny.tests.mockers import CONTEXTS_SHARED_MAX_1 as contexts1
        from maxbunny.tests.mockers import CONTEXTS_SHARED_MAX_2 as contexts2
        from maxbunny.tests.mockers import SINGLE_USER as users

        http_mock_info()

        http_mock_users(users)
        http_mock_contexts(contexts1)
        http_mock_post_user_activity()

        http_mock_users(users, uri='tests.local2')
        http_mock_contexts(contexts2, uri='tests.local2')
        http_mock_post_user_activity(uri='tests.local2')

        runner = MockRunner('tweety', 'maxbunny.ini', count=2)
        consumer = __consumer__(runner)
        consumer.process(message)

        self.assertEqual(len(consumer.logger.infos), 2)
        self.assertEqual(len(consumer.logger.warnings), 1)

        self.assertTrue(consumer.logger.infos[0].startswith('Processing tweet'))
        self.assertTrue(consumer.logger.infos[1].startswith('Successfully posted'))

        self.assertIn(contexts1[0]['url'], consumer.logger.infos[1])
        self.assertEqual(consumer.logger.warnings[0], MULTIPLE_GLOBAL_HASHTAGS_FOUND.format(maxservers=['testing2'], **message['d']))
