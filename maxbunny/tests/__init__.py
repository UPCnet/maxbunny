from maxbunny.clients import MaxClientsWrapper
from maxclient.rest import MaxClient as RestMaxClient
import ConfigParser
import os
import sys
import unittest
import socket

from pamqp import specification


TESTS_PATH = os.path.dirname(sys.modules['maxbunny.tests'].__file__)
RABBIT_URL = "amqp://guest:guest@localhost:5672"
TEST_VHOST_URL = '{}/tests'.format(RABBIT_URL)


def get_storing_logger(self):
    return MockLogger()


class MockRabbitServer(object):
    def __init__(self, message, mid):
        self.messages = [(message,)]
        self.messages[0][0].update({
            'd': {},
            'a': 'k',
            's': 'b'
        })
        self.messages[0][0]['d']['id'] = mid

    def get_all(self, queue):
        return self.messages


class MockConnection(object):

    def __init__(self, *args, **kwargs):
        pass

    def channel(self):
        return Channel()


class Channel(object):
    pass

    def _write_frames(self, *args, **kwargs):
        pass

    def _wait_for_confirmation(self, *args, **kwargs):
        return specification.Basic.Ack()

    def __getattr__(self, name):
        return 1


class MockLogger(object):
    def __init__(self):
        self.infos = []
        self.warnings = []

    def info(self, message):
        print message
        self.infos.append(message)

    def warning(self, message):
        print message

        self.warnings.append(message)
        print self.warnings


class MockRunner(object):
    rabbitmq_server = TEST_VHOST_URL
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
        else:
            # Meant to be raised in tests that test exceptions,
            # if the exception does not raise
            self.assertEqual('', 'Did not raise')   # pragma: no cover


def is_rabbit_active():
    active = False
    try:
        socket.socket().bind(('localhost', 5672))
    except:
        active = True
    return active
