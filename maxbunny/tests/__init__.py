from maxclient.rest import MaxClient

import ConfigParser
import os
import sys
import unittest

TESTS_PATH = os.path.dirname(sys.modules['maxbunny.tests'].__file__)
RESTRICTED_USER = 'restricted'
RESTRICTED_TOKEN = '-------------dummy---------------------'


# Patch consumer logger to store logs in a consumer var
from maxbunny.consumer import BunnyConsumer


def get_storing_logger(self):
    return MockLogger()

BunnyConsumer.configure_logger = get_storing_logger


class MockLogger(object):
    def __init__(self):
        self.infos = []
        self.warnings = []

    def info(self, message):
        self.infos.append(message)

    def warning(self, message):
        self.warnings.append(message)


class TestClientsMocker(dict):
    def __init__(self):
        client = MaxClient('http://tests.local', debug=True)
        client.metadata = {'hashtag': 'testing', 'language': 'ca'}
        client.setActor(RESTRICTED_USER)
        client.setToken(RESTRICTED_TOKEN)

        self['tests'] = client

    def get_all(self):
        return self.items()

    def client_ids_by_hashtag(self):
        mapping = {}
        for instance_id, client in self.items():
            mapping[client.metadata['hashtag']] = instance_id
        return mapping


class RabbitpyMockMessage(dict):
    def __init__(self, message):
        self.update(message)

    def json(self):
        return dict(self)


class MockRunner(object):
    rabbitmq_server = ''
    workers_ready = None

    def __init__(self, consumer_name, ini_file):
        self.debug = consumer_name
        self.config = ConfigParser.ConfigParser()
        self.config.read('{}/{}'.format(TESTS_PATH, 'maxbunny.ini'))
        self.clients = TestClientsMocker()


class MaxBunnyTestCase(unittest.TestCase):
    def assertRaisesWithMessage(self, exc_type, msg, func, *args, **kwargs):
        try:
            func(*args, **kwargs)
            self.assertFail()
        except Exception as inst:
            self.assertEqual(exc_type, inst.__class__)
            self.assertEqual(inst.message, msg)
