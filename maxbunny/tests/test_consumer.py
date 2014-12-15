from maxbunny.consumer import BunnyConsumer
from maxbunny.consumer import BunnyMessageCancel
from maxbunny.tests import get_storing_logger
from maxbunny.tests import MaxBunnyTestCase
from maxbunny.tests import MockRunner
from maxbunny.tests import TEST_VHOST_URL
from maxcarrot import RabbitClient
from multiprocessing import Process

from mock import patch


class TestConsumer(BunnyConsumer):
    queue = 'tests'

    def process(self, message):
        raise BunnyMessageCancel('')


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

    def tearDown(self):
        self.log_patch.stop()

        self.server.get_all('push')
        self.server.disconnect()

    def test_consumer(self):

        runner = MockRunner('tweety', 'maxbunny.ini', 'instances.ini')
        consumer = TestConsumer(runner)

        self.server.send('', '{}', routing_key='tests')
        consumer.logger.warning('TEST')

        p = Process(target=consumer.consume, kwargs={"nowait": True})
        p.start()

        import ipdb;ipdb.set_trace()
