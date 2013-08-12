# -*- coding: utf-8 -*-
from maxclient import MaxClient
from maxbunny.tweety import TweetyMessage
from maxbunny.tests.mockers import contexts, users, response_followed_user, response_hashtag

import ConfigParser
import httpretty
import json
import unittest
import os


class bunnyMock(object):
    def __init__(self):
        conf_dir = os.path.dirname(__file__)
        self.restricted_username = 'victor.fernandez'
        self.restricted_token = 'uj5v4XrWMxGP25CN3pAE39mYCL7cwBMV'

        self.config = ConfigParser.ConfigParser()
        self.config.read(os.path.join(conf_dir, "maxbunny.ini"))

        self.maxservers_settings = [maxserver for maxserver in self.config.sections() if maxserver.startswith('max_')]

        # Instantiate a maxclient for each maxserver
        self.maxclients = {}
        for maxserver in self.maxservers_settings:
            maxclient = MaxClient(url=self.config.get(maxserver, 'server'), oauth_server=self.config.get(maxserver, 'oauth_server'))
            maxclient.setActor(self.restricted_username)
            maxclient.setToken(self.restricted_token)
            self.maxclients[maxserver] = maxclient


class TweetyTests(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @httpretty.activate
    def test_tweet_from_followed_user(self):
        httpretty.register_uri(httpretty.GET, "http://localhost:8081/contexts",
                           body=json.dumps(contexts),
                           status=200,
                           content_type="application/json")
        httpretty.register_uri(httpretty.GET, "http://localhost:8081/people",
                           body=json.dumps(users),
                           status=200,
                           content_type="application/json")
        httpretty.register_uri(httpretty.POST, "http://localhost:8081/contexts/8523ab8065a69338d5006c34310dc8d2c0179ebb/activities",
                           body=json.dumps(response_followed_user),
                           status=201,
                           content_type="application/json")
        bunny = bunnyMock()
        body = json.dumps({'stid': '123123123', 'author': 'sunbit', 'message': 'Hellooooo'})
        responses = TweetyMessage(bunny, body).process()
        self.failUnless(responses)
        for response in responses:
            self.assertIn('201', response)

    @httpretty.activate
    def test_tweet_with_a_hashtag(self):
        httpretty.register_uri(httpretty.GET, "http://localhost:8081/contexts",
                           body=json.dumps(contexts),
                           status=200,
                           content_type="application/json")
        httpretty.register_uri(httpretty.GET, "http://localhost:8081/people",
                           body=json.dumps(users),
                           status=200,
                           content_type="application/json")
        httpretty.register_uri(httpretty.POST, "http://localhost:8081/people/victor.fernandez/activities",
                           body=json.dumps(response_hashtag),
                           status=201,
                           content_type="application/json")
        bunny = bunnyMock()
        body = json.dumps({'stid': '123123123', 'author': 'sneridagh', 'message': 'This is a post with #upc #thehashtag'})
        responses = TweetyMessage(bunny, body).process()
        self.failUnless(responses)
        for response in responses:
            self.assertIn('201', response)

    @httpretty.activate
    def test_tweet_with_invalid_hashtag(self):
        httpretty.register_uri(httpretty.GET, "http://localhost:8081/contexts",
                           body=json.dumps(contexts),
                           status=200,
                           content_type="application/json")
        httpretty.register_uri(httpretty.GET, "http://localhost:8081/people",
                           body=json.dumps(users),
                           status=200,
                           content_type="application/json")
        httpretty.register_uri(httpretty.POST, "http://localhost:8081/people/victor.fernandez/activities",
                           body=json.dumps(response_hashtag),
                           status=201,
                           content_type="application/json")
        bunny = bunnyMock()
        body = json.dumps({'stid': '123123123', 'author': 'sneridagh', 'message': 'This is a post with #upc #other'})
        response = TweetyMessage(bunny, body).process()
        self.assertIn('404', response)

    @httpretty.activate
    def test_tweet_with_only_a_global_hashtag(self):
        httpretty.register_uri(httpretty.GET, "http://localhost:8081/contexts",
                           body=json.dumps(contexts),
                           status=200,
                           content_type="application/json")
        httpretty.register_uri(httpretty.GET, "http://localhost:8081/people",
                           body=json.dumps(users),
                           status=200,
                           content_type="application/json")
        httpretty.register_uri(httpretty.POST, "http://localhost:8081/people/victor.fernandez/activities",
                           body=json.dumps(response_hashtag),
                           status=201,
                           content_type="application/json")
        bunny = bunnyMock()
        body = json.dumps({'stid': '123123123', 'author': 'sneridagh', 'message': 'Només amb el hashtag global... bug or feature? #upc'})
        response = TweetyMessage(bunny, body).process()
        self.assertIn('501', response)

    @httpretty.activate
    def test_tweet_with_hashtag_no_registered_user(self):
        httpretty.register_uri(httpretty.GET, "http://localhost:8081/contexts",
                           body=json.dumps(contexts),
                           status=200,
                           content_type="application/json")
        httpretty.register_uri(httpretty.GET, "http://localhost:8081/people",
                           body=json.dumps(users),
                           status=200,
                           content_type="application/json")
        bunny = bunnyMock()
        body = json.dumps({'stid': '123123123', 'author': 'barackobama', 'message': 'Hellooooo #upc #thehashtag'})
        response = TweetyMessage(bunny, body).process()
        self.assertIn('404', response)
