from maxbunny.clients import MaxClientsWrapper
from maxclient.rest import MaxClient as RestMaxClient
import ConfigParser
import os
import sys
import unittest


TESTS_PATH = os.path.dirname(sys.modules['maxbunny.tests'].__file__)

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


class MockRunner(object):
    rabbitmq_server = ''
    workers_ready = None

    def __init__(self, consumer_name, ini_file, instances_ini):
        self.debug = consumer_name
        self.config = ConfigParser.ConfigParser()
        self.config.read('{}/{}'.format(TESTS_PATH, 'maxbunny.ini'))
        self.clients = MaxClientsWrapper(
            '{}/{}'.format(TESTS_PATH, instances_ini),
            'default',
            debug=os.environ.get('debug', False),
            client_class=RestMaxClient
        )


class MaxBunnyTestCase(unittest.TestCase):
    def assertRaisesWithMessage(self, exc_type, msg, func, *args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as inst:
            self.assertEqual(exc_type, inst.__class__)
            self.assertEqual(inst.message, msg)
