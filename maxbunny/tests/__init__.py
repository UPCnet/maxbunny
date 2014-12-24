from maxbunny.clients import MaxClientsWrapper
from maxclient.rest import MaxClient as RestMaxClient
import ConfigParser
import os
import sys
import unittest
import socket
import thread

from pamqp import specification
import tempfile

TESTS_PATH = os.path.dirname(sys.modules['maxbunny.tests'].__file__)
RABBIT_URL = "amqp://guest:guest@localhost:5672"
TEST_VHOST_URL = '{}/tests'.format(RABBIT_URL)

# =============================================================
#                    Logging mockers
# =============================================================


class MockLogger(object):
    """
        Fake logger to easily access logged strings from tests

        It behaves like a regular python logger, but stores logs on
        temporary files, and has property methods to access the log contents
        as an array
    """
    def __init__(self):
        temp_folder = tempfile.gettempdir()
        self.warnings_file = '{}/warnings'.format(temp_folder)
        self.infos_file = '{}/infos'.format(temp_folder)
        self.errors_file = '{}/errors'.format(temp_folder)
        open(self.warnings_file, 'w').write('')
        open(self.infos_file, 'w').write('')
        open(self.errors_file, 'w').write('')

    def info(self, message):
        open(self.infos_file, 'a').write(message.rstrip('\n') + '\n')

    def warning(self, message):
        open(self.warnings_file, 'a').write(message.rstrip('\n') + '\n')

    def error(self, message):
        open(self.errors_file, 'a').write(message.rstrip('\n') + '\n')

    @staticmethod
    def readlines(filename):
        content = open(filename).read()
        return [line for line in content.split('\n') if line]

    @property
    def infos(self):
        return self.readlines(self.infos_file)

    @property
    def warnings(self):
        return self.readlines(self.warnings_file)

    @property
    def errors(self):
        return self.readlines(self.errors_file)


def get_storing_logger(self):
    """
        Returns a mock logger.
    """
    return MockLogger()


# =============================================================
#                    RabbitPy Mockers
# =============================================================


class MockConnection(object):
    """
        Fakes a rabbitpy.Connection.

        It returns a fake Channel object, and can be told
        to fail with an exception before the Channel is returned
    """

    def __init__(self, *args, **kwargs):
        self.fail = kwargs.pop('fail', 0)

    def channel(self):
        if self.fail > 0:
            self.fail -= 1
            raise Exception('Mocked RabbitMQ Server not found')
        return Channel()

    def close(self):
        pass

queue_used = False


class MockQueue(object):
    """
        Fakes a rabbitpy.Queue with messages defined in content param.
    """

    def __init__(self, channel, name, content=[], *args, **kwargs):
        self.content = content
        self.first = kwargs.get('first', self.content)

    def consume_messages(self):
        """
            Returns items on self.content as a generator. On the first
            execution, uses self.first list. If a list item is an exception
            raises it instead of yielding
        """
        global queue_used
        queue_content = self.content if queue_used else self.first
        queue_used = True
        for item in queue_content:
            if isinstance(item, BaseException) or isinstance(item, thread.error):
                raise item
            else:
                yield item


class Channel(object):
    """
        Fakes a rabbitpy.Channel object.
    """

    # def _write_frames(self, *args, **kwargs):
    #     pass

    # def _wait_for_confirmation(self, *args, **kwargs):
    #     return specification.Basic.Ack()

    # def __getattr__(self, name):
    #     return 1


# =============================================================
#                    smtlip Mockers
# =============================================================

sent = []


class MockEmailMessage(object):
    """
        Fakes an smtplib.Message
    """
    def __init__(self, from_address, to_address, fullmessage):
        self.from_address = from_address
        self.to_address = to_address
        self.fullmessage = fullmessage


class MockSMTP(object):
    """
        Fakes an stmplib.SMTP Server.
    """
    def __init__(self, address):
        self.address = address

    def sendmail(self, from_address, to_address, fullmessage):
        """
            Stores mail sent in a global var.

            Sent messages can be accessed by importing maxbunny.tests.sent.
        """
        global sent
        sent.append(MockEmailMessage(from_address, to_address, fullmessage))
        return []

# =============================================================
#                    APNS Mockers
# =============================================================

apns_response = {}


class MockAPNSSession(object):
    """
        Mocks an apnsclient.Session object.
    """
    def get_connection(*args, **kwargs):
        return True


class MockAPNs(object):
    """
        Mocks an apnsclient.APNs Server object.

        When a push messages sent trough this mock, it
        responds with a custom-defined response particular to
        each test
    """
    def __init__(self, *args, **kwargs):
        pass

    def send(self, *args, **kwargs):
        """
            Returns or raises an exception, as defined
            on apns_response global var, that must be
            set just before using this method
        """
        global apns_response
        if isinstance(apns_response, Exception):
            raise apns_response
        else:
            return apns_response


def set_apns_response(response):
    """
        Sets the response that will be used on MockAPNs.send calls.
    """
    global apns_response
    apns_response = response


# =============================================================
#                    gcmclient Mockers
# =============================================================

gcm_response = {}


class MockGCM(object):
    def __init__(self, *args, **kwargs):
        """
            Mocks an gcmclient.GCM Server object.

            When a push messages sent trough this mock, it
            responds with a custom-defined response particular to
            each test
        """
        pass

    def send(self, *args, **kwargs):
        """
            Returns or raises an exception, as defined
            on gcm_response global var, that must be
            set just before using this method
        """
        global gcm_response
        if isinstance(gcm_response, Exception):
            raise gcm_response
        else:
            return gcm_response


def set_gcm_response(response):
    """
        Sets the response that will be used on MockAPNs.send calls.
    """
    global gcm_response
    gcm_response = response


# =============================================================
#                    Maxbunny Mockers
# =============================================================

class MockRunner(object):
    """
        Mocks a maxbunny.runner.BunnyRunner object.

        This is provided to be able to test features of the main
        consumer algorithm and the particular consumer scenarios,
        without all the multiprocessing and process spawining stuff
        of the real BunnyRunner
    """
    rabbitmq_server = TEST_VHOST_URL
    workers_ready = None

    def __init__(self, consumer_name, ini_file, instances_ini, cloudapis_ini='nocloudapis.ini', logging_folder=None, wait_signal=None):
        self.debug = consumer_name
        self.logging_folder = logging_folder
        self.config = ConfigParser.ConfigParser()
        self.config.read('{}/{}'.format(TESTS_PATH, ini_file))
        if wait_signal:
            self.workers_ready = wait_signal

        self.cloudapis = ConfigParser.ConfigParser()
        self.cloudapis.read('{}/{}'.format(TESTS_PATH, cloudapis_ini))

        self.clients = MaxClientsWrapper(
            '{}/{}'.format(TESTS_PATH, instances_ini),
            'default',
            debug=os.environ.get('debug', False),
            client_class=RestMaxClient
        )


class MaxBunnyTestCase(unittest.TestCase):
    """
        Provides common features for all maxbunny tests.
    """
    def assertRaisesWithMessage(self, exc_type, msg, func, *args, **kwargs):
        """
            Asserts if func raises with the expect exc_type and msg.
            Fails when any of both don't match.
        """
        try:
            func(*args, **kwargs)
        except Exception as inst:
            self.assertEqual(exc_type, inst.__class__)
            self.assertEqual(inst.message, msg)
        else:
            # Meant to be raised in tests that test exceptions,
            # if the exception does not raise
            self.assertEqual('', 'Did not raise')   # pragma: no cover
