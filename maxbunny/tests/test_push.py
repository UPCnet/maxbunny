# -*- coding: utf-8 -*-
from apnsclient import Session
from maxclient import MaxClient
from maxbunny.push import PushMessage
from maxbunny.tests.mockers import user_tokens

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

        self.ios_session = Session()


class TweetyTests(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @httpretty.activate
    def test_push_apple(self):
        httpretty.register_uri(httpretty.GET, "http://localhost:8081/conversations/5452452034992348/tokens",
                           body=json.dumps(user_tokens),
                           status=200,
                           content_type="application/json")
        bunny = bunnyMock()
        message = {
            'conversation': '5452452034992348',
            'message': 'Hi! this is a test of a push message',
            'username': 'victor.fernandez',
            'displayName': 'Victor Fernandez de Alba',
            'messageID': '213452532',
            'server_id': 'max_default'
        }
        body = json.dumps(message)
        response = PushMessage(bunny, body).process()
        self.assertIn('Successfully', response)
