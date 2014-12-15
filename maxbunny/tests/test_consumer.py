from maxbunny.consumer import BunnyConsumer
from maxbunny.consumer import BunnyMessageCancel
from maxbunny.tests import get_storing_logger
from maxbunny.tests import MaxBunnyTestCase
from maxbunny.tests import MockRunner
from maxbunny.tests import TEST_VHOST_URL
from maxcarrot import RabbitClient
from threading import Thread

from mock import patch
from time import sleep


class TestConsumer(BunnyConsumer):
    queue = 'tests'

    def __init__(self, *args, **kwargs):
        self.exception = kwargs.pop('exception', None)
        super(TestConsumer, self).__init__(*args, **kwargs)

    def process(self, message):
        if self.exception:
            raise self.exception

    def remote(self):
        conn = self.channels[self.wid]['connection']
        return conn._io._remote_name


class ConsumerThread(Thread):
    def __init__(self, consumer):
        Thread.__init__(self)
        self.consumer = consumer

    def run(self):
        self.consumer.consume(nowait=True)


class ConsumerTests(MaxBunnyTestCase):
    def setUp(self):
        self.log_patch = patch('maxbunny.consumer.BunnyConsumer.configure_logger', new=get_storing_logger)
        self.log_patch.start()
        self.server = RabbitClient(TEST_VHOST_URL)
        self.server.management.cleanup(delete_all=True)
        self.server.declare()
        self.server.ch.queue.declare(
            queue='tests',
            durable=True,
            auto_delete=False
        )
        self.process = None

    def tearDown(self):
        self.log_patch.stop()

        self.server.get_all('tests')
        self.server.disconnect()

        try:
            self.process.terminate()
        except:
            pass  # pragma: no cover

    def test_consumer_drop_no_uuid(self):

        runner = MockRunner('tweety', 'maxbunny.ini', 'instances.ini')
        consumer = TestConsumer(runner, exception=BunnyMessageCancel('Testing message drop'))
        self.process = ConsumerThread(consumer)

        self.server.send('', '{}', routing_key='tests')
        self.process.start()

        sleep(0.2)  # Leave a minimum time to message to reach rabbitmq
        queued = self.server.get_all('tests')

        self.assertEqual(len(queued), 0)
        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 1)
        self.assertEqual(consumer.logger.warnings[0], 'Message dropped (NO_UUID), reason: Testing message drop')

        self.server.management.force_close(consumer.remote())
