from maxbunny.consumer import BunnyConsumer
from maxbunny.consumer import BunnyMessageCancel
from maxbunny.consumer import BunnyMessageRequeue
from maxbunny.tests import get_storing_logger
from maxbunny.tests import MockConnection
from maxbunny.tests import MockQueue
from maxbunny.tests import MaxBunnyTestCase
from maxbunny.tests import MockRunner
from maxbunny.tests import MockSMTP
from maxbunny.tests import TEST_VHOST_URL
from maxcarrot import RabbitClient
from threading import Thread

from mock import patch
from time import sleep
from functools import partial

import os


class TestConsumer(BunnyConsumer):
    name = 'testconsumer'
    queue = 'tests'

    def __init__(self, runner, return_value=None, **kwargs):
        self.return_value = return_value
        self.second_return_value = kwargs.pop('after', self.return_value)
        self.executed = False
        super(TestConsumer, self).__init__(runner, **kwargs)

    def process(self, message):
        return_value = self.return_value if not self.executed else self.second_return_value
        self.executed = True

        if isinstance(return_value, Exception):
            raise return_value
        else:
            return return_value

    def remote(self):
        conn = self.channels[self.wid]['connection']
        return conn._io._remote_name


class ConsumerThread(Thread):
    def __init__(self, consumer):
        Thread.__init__(self)
        self.consumer = consumer

    def run(self):
        self.consumer.consume(nowait=True)


class ConsumerTestsWithLogging(MaxBunnyTestCase):

    def tearDown(self):
        os.remove('/tmp/testconsumer.log')

    def test_logger_configuration(self):
        runner = MockRunner('tests', 'maxbunny.ini', 'instances.ini', logging_folder='/tmp')
        consumer = TestConsumer(runner)
        consumer.logger.info('Test log line')

        self.assertEqual(consumer.logger.name, 'testconsumer')
        self.assertEqual(consumer.logger.handlers[0].baseFilename, '/tmp/testconsumer.log')
        self.assertIn('Test log line', open('/tmp/testconsumer.log').read())


class ConsumerTestsWithRabbitMQMocked(MaxBunnyTestCase):
    def setUp(self):
        self.log_patch = patch('maxbunny.consumer.BunnyConsumer.configure_logger', new=get_storing_logger)
        self.log_patch.start()

        self.rabbit_patch = patch('rabbitpy.Connection', new=partial(MockConnection, fail=2))
        self.rabbit_patch.start()

        self.rabbit_queue_patch = patch('rabbitpy.Queue', MockQueue)
        self.rabbit_queue_patch.start()

    def tearDown(self):
        self.log_patch.stop()
        self.rabbit_patch.stop()
        self.rabbit_queue_patch.stop()

    def test_rabbitm_start_disconnected_reconnects(self):
        runner = MockRunner('tests', 'maxbunny.ini', 'instances.ini')
        consumer = TestConsumer(runner)
        consumer.consume(nowait=True)
        self.assertEqual(consumer.logger.infos[0], 'Waiting for rabbitmq...')
        self.assertEqual(consumer.logger.infos[1], 'Connection with RabbitMQ recovered!')
        self.assertEqual(consumer.logger.infos[2], 'Worker MainProcess ready')


class ConsumerTests(MaxBunnyTestCase):
    def setUp(self):
        # Resets the global that holds the mocked stmp sent messages
        import maxbunny.tests
        maxbunny.tests.sent = []

        self.log_patch = patch('maxbunny.consumer.BunnyConsumer.configure_logger', new=get_storing_logger)
        self.log_patch.start()

        self.smtp_patch = patch('smtplib.SMTP', new=MockSMTP)
        self.smtp_patch.start()

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
        self.smtp_patch.stop()

        self.server.get_all('tests')
        self.server.disconnect()

        try:
            self.process.terminate()
        except:
            pass  # pragma: no cover

    def test_consumer_drop_no_uuid(self):
        """
            Given a invalid non-json message
            When the consumer loop processes the message
            And the message triggers a Cancel exception
            Then the message is dropped
            And a warning is logged
            And the channel remains Open
        """
        runner = MockRunner('tests', 'maxbunny.ini', 'instances.ini')
        consumer = TestConsumer(runner, BunnyMessageCancel('Testing message drop'))
        self.process = ConsumerThread(consumer)

        self.server.send('', '', routing_key='tests')
        self.process.start()

        sleep(0.3)  # give a minum time to mail to be sent
        from maxbunny.tests import sent  # MUST import sent here to get current sent mails,

        self.assertEqual(len(sent), 1)
        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 1)
        self.assertTrue(self.process.isAlive())
        self.assertEqual(consumer.logger.warnings[0], 'Message dropped (NO_UUID), reason: Testing message drop')

        self.server.management.force_close(consumer.remote())

        sleep(0.2)  # Leave a minimum time to rabbitmq to release messages
        queued = self.server.get_all('tests')
        self.assertEqual(len(queued), 0)

    def test_consumer_drops_on_requeue_exception_without_uuid(self):
        """
            Given a message without UUID field
            When the consumer loop processes the message
            And the message triggers a Requeue exception
            Then the message is requeued
            And a warning is logged
            And the channel remains Open
            And a mail notification is sent
        """
        runner = MockRunner('tests', 'maxbunny.ini', 'instances.ini')
        consumer = TestConsumer(runner, BunnyMessageRequeue('Test requeueing'))
        self.process = ConsumerThread(consumer)

        self.server.send('', '{}', routing_key='tests')
        self.process.start()

        sleep(0.3)  # give a minum time to mail to be sent
        from maxbunny.tests import sent  # MUST import sent here to get current sent mails,

        self.assertEqual(len(sent), 1)
        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 1)
        self.assertTrue(self.process.isAlive())
        self.assertEqual(consumer.logger.warnings[0], 'Message dropped (NO_UUID), reason: Test requeueing')

        self.server.management.force_close(consumer.remote())

        sleep(0.2)  # Leave a minimum time to rabbitmq to release messages
        queued = self.server.get_all('tests')
        self.assertEqual(len(queued), 0)

    def test_consumer_drop_with_uuid(self):
        """
            Given a message with UUID field
            When the consumer loop processes the message
            And the message triggers a Cancel exception
            Then the message is dropped
            And a warning is logged
            And the channel remains Open
            And no mail notification is sent
        """
        runner = MockRunner('tests', 'maxbunny.ini', 'instances.ini')
        consumer = TestConsumer(runner, BunnyMessageCancel('Testing message drop', notify=False))
        self.process = ConsumerThread(consumer)

        self.server.send('', '{"g": "0123456789"}', routing_key='tests')
        self.process.start()

        sleep(0.3)  # give a minum time to mail to be sent
        from maxbunny.tests import sent  # MUST import sent here to get current sent mails,

        self.assertEqual(len(sent), 0)
        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 1)
        self.assertTrue(self.process.isAlive())
        self.assertEqual(consumer.logger.warnings[0], 'Message dropped, reason: Testing message drop')

        self.server.management.force_close(consumer.remote())

        sleep(0.2)  # Leave a minimum time to rabbitmq to release messages
        queued = self.server.get_all('tests')
        self.assertEqual(len(queued), 0)

    def test_consumer_drop_with_notification(self):
        """
            Given a message with UUID field
            When the consumer loop processes the message
            And the message triggers a Cancel exception
            Then the message is dropped
            And a warning is logged
            And the channel remains Open
            And a mail notification is sent
        """
        runner = MockRunner('tests', 'maxbunny.ini', 'instances.ini')
        consumer = TestConsumer(runner, BunnyMessageCancel('Testing message drop', notify=True))
        self.process = ConsumerThread(consumer)

        self.server.send('', '{"g": "0123456789"}', routing_key='tests')
        self.process.start()

        sleep(0.3)  # give a minum time to mail to be sent
        from maxbunny.tests import sent  # MUST import sent here to get current sent mails,

        self.assertEqual(len(sent), 1)
        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 1)
        self.assertTrue(self.process.isAlive())
        self.assertEqual(consumer.logger.warnings[0], 'Message dropped, reason: Testing message drop')

        self.server.management.force_close(consumer.remote())

        sleep(0.2)  # Leave a minimum time to rabbitmq to release messages
        queued = self.server.get_all('tests')
        self.assertEqual(len(queued), 0)

    def test_consumer_drop_no_recipient(self):
        """
            Given a message with UUID field
            And a missing recipients smtp setting
            When the consumer loop processes the message
            And the message triggers a Cancel exception
            Then the message is dropped
            And a warning is logged
            And the channel remains Open
            And a mail notification is not sent
        """
        runner = MockRunner('tests', 'maxbunny-norecipients.ini', 'instances.ini')
        consumer = TestConsumer(runner, BunnyMessageCancel('Testing message drop', notify=True))
        self.process = ConsumerThread(consumer)

        self.server.send('', '{"g": "0123456789"}', routing_key='tests')
        self.process.start()

        sleep(0.3)  # give a minum time to mail to be sent
        from maxbunny.tests import sent  # MUST import sent here to get current sent mails,

        self.assertEqual(len(sent), 0)
        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 1)
        self.assertTrue(self.process.isAlive())
        self.assertEqual(consumer.logger.warnings[0], 'Message dropped, reason: Testing message drop')

        self.server.management.force_close(consumer.remote())

        sleep(0.2)  # Leave a minimum time to rabbitmq to release messages
        queued = self.server.get_all('tests')
        self.assertEqual(len(queued), 0)

    def test_consumer_drop_on_max_non_5xx_error(self):
        """
            Given a message with UUID field
            When the consumer loop processes the message
            And the message triggers a RequestError with status code different from 5xx
            Then the message is dropped
            And a warning is logged
            And the channel remains Open
            And a mail notification is sent
        """
        from maxclient.client import RequestError
        runner = MockRunner('tests', 'maxbunny.ini', 'instances.ini')
        consumer = TestConsumer(runner, RequestError(401, 'Unauthorized'))
        self.process = ConsumerThread(consumer)

        self.server.send('', '{"g": "0123456789"}', routing_key='tests')
        self.process.start()

        sleep(0.3)  # give a minum time to mail to be sent
        from maxbunny.tests import sent  # MUST import sent here to get current sent mails,

        self.assertEqual(len(sent), 1)
        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 1)
        self.assertTrue(self.process.isAlive())
        self.assertEqual(consumer.logger.warnings[0], 'Message dropped, reason: Max server error: Unauthorized')

        self.server.management.force_close(consumer.remote())

        sleep(0.2)  # Leave a minimum time to rabbitmq to release messages
        queued = self.server.get_all('tests')
        self.assertEqual(len(queued), 0)

    def test_consumer_drop_on_maxcarrot_exception(self):
        """
            Given a message with UUID field
            When the consumer loop processes the message
            And the message triggers a MaxCarrotParsingError
            Then the message is dropped
            And a warning is logged
            And the channel remains Open
            And a mail notification is sent
        """
        from maxcarrot.message import MaxCarrotParsingError
        runner = MockRunner('tests', 'maxbunny.ini', 'instances.ini')
        consumer = TestConsumer(runner, MaxCarrotParsingError())
        self.process = ConsumerThread(consumer)

        self.server.send('', '{"g": "0123456789"}', routing_key='tests')
        self.process.start()

        sleep(0.3)  # give a minum time to mail to be sent
        from maxbunny.tests import sent  # MUST import sent here to get current sent mails,

        self.assertEqual(len(sent), 1)
        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 1)
        self.assertTrue(self.process.isAlive())
        self.assertEqual(consumer.logger.warnings[0], 'Message dropped, reason: MaxCarrot Parsing error')

        self.server.management.force_close(consumer.remote())

        sleep(0.2)  # Leave a minimum time to rabbitmq to release messages
        queued = self.server.get_all('tests')
        self.assertEqual(len(queued), 0)

    def test_consumer_requeues_on_max_5xx_error(self):
        """
            Given a message with UUID field
            When the consumer loop processes the message
            And the message triggers a RequestError with status code different from 5xx
            Then the message is requeued
            And a warning is logged
            And the channel remains Open
            And a mail notification is sent
        """
        from maxclient.client import RequestError
        runner = MockRunner('tests', 'maxbunny.ini', 'instances.ini')
        consumer = TestConsumer(runner, RequestError(500, 'Internal Server Error'))
        self.process = ConsumerThread(consumer)

        self.server.send('', '{"g": "0123456789"}', routing_key='tests')
        self.process.start()

        sleep(0.3)  # give a minum time to mail to be sent
        from maxbunny.tests import sent  # MUST import sent here to get current sent mails,

        self.assertEqual(len(sent), 1)
        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 1)
        self.assertTrue(self.process.isAlive())
        self.assertEqual(consumer.logger.warnings[0], 'Message 0123456789 reueued, reason: Max server error: Internal Server Error')

        self.server.management.force_close(consumer.remote())

        sleep(0.2)  # Leave a minimum time to rabbitmq to release messages

        queued = self.server.get_all('tests')
        self.assertEqual(len(queued), 1)

    def test_consumer_requeues_on_requeue_exception(self):
        """
            Given a message with UUID field
            When the consumer loop processes the message
            And the message triggers a Requeue exception
            Then the message is requeued
            And a warning is logged
            And the channel remains Open
            And a mail notification is sent
            And the id of the queued message is stored
        """
        runner = MockRunner('tests', 'maxbunny.ini', 'instances.ini')
        consumer = TestConsumer(runner, BunnyMessageRequeue('Test requeueing'))
        self.process = ConsumerThread(consumer)

        self.server.send('', '{"g": "0123456789"}', routing_key='tests')
        self.process.start()

        sleep(0.3)  # give a minum time to mail to be sent
        from maxbunny.tests import sent  # MUST import sent here to get current sent mails,

        self.assertEqual(len(sent), 1)
        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 1)
        self.assertTrue(self.process.isAlive())
        self.assertEqual(consumer.logger.warnings[0], 'Message 0123456789 reueued, reason: Test requeueing')

        self.server.management.force_close(consumer.remote())

        sleep(0.2)  # Leave a minimum time to rabbitmq to release messages

        queued = self.server.get_all('tests')
        self.assertEqual(len(queued), 1)
        self.assertEqual(len(consumer.requeued), 1)
        self.assertIn('0123456789', consumer.requeued)

    def test_consumer_requeues_on_requeue_exception_unqueues_after(self):
        """
            Given a message with UUID field
            When the consumer loop processes the message
            And the first time the message triggers a Requeue exception
            And the second time the message is succesfully processed
            Then the message is unqueued the second time
            And a warning is logged
            And the channel remains Open
            And a mail notification is sent
            And the id is removed from queued ones
        """
        runner = MockRunner('tests', 'maxbunny.ini', 'instances.ini')
        consumer = TestConsumer(runner, BunnyMessageRequeue('Test requeueing'), after=None)
        self.process = ConsumerThread(consumer)

        self.server.send('', '{"g": "0123456789"}', routing_key='tests')
        self.process.start()

        sleep(0.3)  # give a minum time to mail to be sent
        from maxbunny.tests import sent  # MUST import sent here to get current sent mails,

        self.assertEqual(len(sent), 1)
        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 1)
        self.assertTrue(self.process.isAlive())
        self.assertEqual(consumer.logger.warnings[0], 'Message 0123456789 reueued, reason: Test requeueing')

        self.server.management.force_close(consumer.remote())

        sleep(0.2)  # Leave a minimum time to rabbitmq to release messages

        queued = self.server.get_all('tests')
        self.assertEqual(len(queued), 0)
        self.assertEqual(len(consumer.requeued), 0)

    def test_consumer_requeues_on_requeue_exception_drops_after(self):
        """
            Given a message with UUID field
            When the consumer loop processes the message
            And the first time the message triggers a Requeue exception
            And the second time the message is triggers a Cancel exception
            Then the message is unqueued the second time
            And a warning is logged
            And the channel remains Open
            And a mail notification is sent
            And the id is removed from queued ones
        """
        runner = MockRunner('tests', 'maxbunny.ini', 'instances.ini')
        consumer = TestConsumer(runner, BunnyMessageRequeue('Test requeueing'), after=BunnyMessageCancel('Testing message drop'))
        self.process = ConsumerThread(consumer)

        self.server.send('', '{"g": "0123456789"}', routing_key='tests')
        self.process.start()

        sleep(0.3)  # give a minum time to mail to be sent
        from maxbunny.tests import sent  # MUST import sent here to get current sent mails,

        self.assertEqual(len(sent), 2)
        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 2)
        self.assertTrue(self.process.isAlive())
        self.assertEqual(consumer.logger.warnings[0], 'Message 0123456789 reueued, reason: Test requeueing')
        self.assertEqual(consumer.logger.warnings[1], 'Message dropped, reason: Testing message drop')

        self.server.management.force_close(consumer.remote())

        sleep(0.2)  # Leave a minimum time to rabbitmq to release messages

        queued = self.server.get_all('tests')
        self.assertEqual(len(queued), 0)
        self.assertEqual(len(consumer.requeued), 0)

    def test_consumer_requeues_on_unknown_exception(self):
        """
            Given a message with UUID field
            When the consumer loop processes the message
            And the message triggers an unknown Exception
            Then the message is requeued
            And a warning is logged
            And the channel remains Open
            And a mail notification is sent
        """
        runner = MockRunner('tests', 'maxbunny.ini', 'instances.ini')
        consumer = TestConsumer(runner, Exception('Unknown exception'))
        self.process = ConsumerThread(consumer)

        self.server.send('', '{"g": "0123456789"}', routing_key='tests')
        self.process.start()

        sleep(0.3)  # give a minum time to mail to be sent
        from maxbunny.tests import sent  # MUST import sent here to get current sent mails,

        self.assertEqual(len(sent), 1)
        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 1)
        self.assertTrue(self.process.isAlive())
        self.assertEqual(consumer.logger.warnings[0], 'Message 0123456789 reueued, reason: Consumer failure: Unknown exception')

        self.server.management.force_close(consumer.remote())

        sleep(0.2)  # Leave a minimum time to rabbitmq to release messages

        queued = self.server.get_all('tests')
        self.assertEqual(len(queued), 1)

    def test_consumer_stops_on_force_stop_connection(self):
        """
            Given a running consumer
            When the rabbitmq connection is closed remotely
            Then the channel closes
            And a warning is logged
        """
        runner = MockRunner('tests', 'maxbunny.ini', 'instances.ini')
        consumer = TestConsumer(runner)
        self.process = ConsumerThread(consumer)
        self.process.start()

        sleep(0.2)  # Leave a minimum life time to consumer

        self.server.management.force_close(consumer.remote(), 'Closed via ')

        sleep(1)  # Leave a minimum time to consumer to stop
        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.errors), 1)
        self.assertFalse(self.process.isAlive())
        self.assertEqual(consumer.logger.errors[0], 'CONNECTION_FORCED - Closed via management plugin')

        sleep(0.2)  # Leave a minimum time to rabbitmq to release messages
        queued = self.server.get_all('tests')
        self.assertEqual(len(queued), 0)

    def test_consumer_success(self):
        """
            Given a message with UUID field
            When the consumer loop processes the message
            And the message suceeds
            Then the message is acks
            And nothing is logged
            And the channel remains Open
            And a no mail notification is sent
        """
        runner = MockRunner('tests', 'maxbunny.ini', 'instances.ini')
        consumer = TestConsumer(runner)
        self.process = ConsumerThread(consumer)

        self.server.send('', '{"g": "0123456789"}', routing_key='tests')
        self.process.start()

        sleep(0.3)  # give a minum time to mail to be sent
        from maxbunny.tests import sent  # MUST import sent here to get current sent mails,

        self.assertEqual(len(sent), 0)
        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 0)
        self.assertTrue(self.process.isAlive())

        self.server.management.force_close(consumer.remote())

        sleep(0.2)  # Leave a minimum time to rabbitmq to release messages
        queued = self.server.get_all('tests')
        self.assertEqual(len(queued), 0)
