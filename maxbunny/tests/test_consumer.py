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
from threading import Thread, Event

from rabbitpy.exceptions import AMQPNotFound
from rabbitpy.exceptions import ConnectionResetException

from mock import patch
from time import sleep
from functools import partial
import thread
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
    def __init__(self, consumer, nowait=True):
        Thread.__init__(self)
        self.consumer = consumer
        self.nowait = nowait

    def run(self):
        self.consumer.consume(nowait=self.nowait)


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
        import maxbunny.tests
        maxbunny.tests.queue_used = False

    def tearDown(self):
        self.log_patch.stop()

    @patch('rabbitpy.Queue', MockQueue)
    @patch('rabbitpy.Connection', new=partial(MockConnection, fail=2))
    def test_worker_reattempts_rabbitmq_start_disconnected(self):
        """
            Given the rabbitmq server is down when the worker starts
            And the worker keeps trying to reconnect
            When the server goes up
            Then the worker starts listening
            And exits normally
        """
        runner = MockRunner('tests', 'maxbunny.ini', 'instances.ini')
        consumer = TestConsumer(runner)
        self.process = ConsumerThread(consumer)
        self.process.start()
        self.process.join()

        self.assertEqual(consumer.logger.infos[0], 'Waiting for rabbitmq...')
        self.assertEqual(consumer.logger.infos[1], 'Connection with RabbitMQ recovered!')
        self.assertEqual(consumer.logger.infos[2], 'Worker MainProcess ready')
        self.assertEqual(consumer.logger.infos[3], 'Exiting Worker MainProcess')

    @patch('rabbitpy.Queue', MockQueue)
    @patch('rabbitpy.Connection', MockConnection)
    def test_worker_waits_for_start_signal(self):
        """
            Given the worker is set to wait for a sync event between workers
            When the worker starts
            And the signal is sent
            Then the worker starts listening
            And exits normally
        """

        wait_signal = Event()
        runner = MockRunner('tests', 'maxbunny.ini', 'instances.ini', wait_signal=wait_signal)
        consumer = TestConsumer(runner)
        self.process = ConsumerThread(consumer, nowait=False)
        self.process.start()

        # Process is waiting the signal to be set, so we won't get anything in the logs
        self.assertEqual(len(consumer.logger.infos), 0)

        # Set the signal and wait for the process to stop and get the log
        wait_signal.set()
        self.process.join()

        self.assertEqual(consumer.logger.infos[0], 'Worker MainProcess ready')
        self.assertEqual(consumer.logger.infos[1], 'Exiting Worker MainProcess')

    @patch('rabbitpy.Queue', new=partial(MockQueue, content=[None]))
    @patch('rabbitpy.Connection', MockConnection)
    def test_worker_receives_non_message_from_queue(self):
        """
            Given the worker is set to wait for a sync event between workers
            When the worker starts
            And the signal is sent
            Then the worker starts listening
            And exits normally
        """
        runner = MockRunner('tests', 'maxbunny.ini', 'instances.ini')
        consumer = TestConsumer(runner)
        self.process = ConsumerThread(consumer)
        self.process.start()
        self.process.join()

        self.assertEqual(consumer.logger.infos[0], 'Worker MainProcess ready')
        self.assertEqual(consumer.logger.infos[1], 'Exiting Worker MainProcess')

    @patch('rabbitpy.Queue', new=partial(MockQueue, content=[KeyboardInterrupt()]))
    @patch('rabbitpy.Connection', MockConnection)
    def test_worker_receives_user_cancelation(self):
        """
            Given the worker is running
            When the user sends a KeyboardInterrupt via ^C
            Then the worker stops the connection
            And worker exits
        """
        runner = MockRunner('tests', 'maxbunny.ini', 'instances.ini')
        consumer = TestConsumer(runner)
        self.process = ConsumerThread(consumer)
        self.process.start()
        self.process.join()

        self.assertEqual(consumer.logger.infos[0], 'Worker MainProcess ready')
        self.assertEqual(consumer.logger.warnings[0], 'User Canceled')
        self.assertEqual(consumer.logger.warnings[1], 'Disconnecting worker MainProcess')

    @patch('rabbitpy.Queue', new=partial(MockQueue, content=[AMQPNotFound('Queue tests not found')]))
    @patch('rabbitpy.Connection', MockConnection)
    def test_rabbitpy_queue_not_found_error(self):
        """
            Given the queue that the worker wants to use don't exists
            When the worker starts the rabbitpy library raises a AMQPNotFound exception
            And worker exits
        """
        runner = MockRunner('tests', 'maxbunny.ini', 'instances.ini')
        consumer = TestConsumer(runner)
        self.process = ConsumerThread(consumer)
        self.process.start()
        self.process.join()

        self.assertEqual(consumer.logger.infos[0], 'Worker MainProcess ready')
        self.assertEqual(consumer.logger.warnings[0], 'AMQPNotFound: Queue tests not found')

    @patch('rabbitpy.Queue', new=partial(MockQueue, first=[ConnectionResetException()]))
    @patch('rabbitpy.Connection', new=partial(MockConnection, fail=2))
    def test_workers_restarts_on_rabbitmq_restart(self):
        """
            Given a running RabbitMQ server
            And a running worker
            When the rabbitmq server is restarted
            Then the worker is restarted too
        """
        runner = MockRunner('tests', 'maxbunny.ini', 'instances.ini')
        consumer = TestConsumer(runner)
        self.process = ConsumerThread(consumer)
        self.process.start()
        self.process.join()

        self.assertEqual(consumer.logger.infos[0], 'Waiting for rabbitmq...')
        self.assertEqual(consumer.logger.infos[1], 'Connection with RabbitMQ recovered!')
        self.assertEqual(consumer.logger.infos[2], 'Worker MainProcess ready')
        self.assertEqual(consumer.logger.infos[3], 'Waiting for rabbitmq...')
        self.assertEqual(consumer.logger.infos[4], 'Connection with RabbitMQ recovered!')
        self.assertEqual(consumer.logger.infos[5], 'Worker MainProcess ready')
        self.assertEqual(consumer.logger.infos[6], 'Exiting Worker MainProcess')
        self.assertEqual(consumer.logger.warnings[0], 'Rabbit Connection Reset')
        self.assertEqual(consumer.logger.warnings[1], 'Restarting Worker MainProcess')

    @patch('rabbitpy.Queue', new=partial(MockQueue, first=[Exception('Not Handled Exception')]))
    @patch('rabbitpy.Connection', MockConnection)
    def test_worker_restarts_on_not_handled_exception(self):
        """
            Given a running worker
            When the consumer process raises an unhandled exception
            Then the worker is restarted
        """
        runner = MockRunner('tests', 'maxbunny.ini', 'instances.ini')
        consumer = TestConsumer(runner)
        self.process = ConsumerThread(consumer)
        self.process.start()
        self.process.join()

        self.assertEqual(consumer.logger.infos[0], 'Worker MainProcess ready')
        self.assertEqual(consumer.logger.infos[1], 'Worker MainProcess ready')
        self.assertEqual(consumer.logger.infos[2], 'Exiting Worker MainProcess')
        self.assertEqual(consumer.logger.warnings[0], "Exception: Not Handled Exception")
        self.assertEqual(consumer.logger.warnings[1], 'Restarting Worker MainProcess')

    @patch('rabbitpy.Queue', new=partial(MockQueue, content=[thread.error('child process')]))
    @patch('rabbitpy.Connection', MockConnection)
    def test_worker_exits_on_exception_caused_by_TERM_signal(self):
        """
            Given a running worker
            When the consumer process raises an exception triggered by a TERM signal
            Then the worker is forced to stop
        """
        runner = MockRunner('tests', 'maxbunny.ini', 'instances.ini')
        consumer = TestConsumer(runner)
        self.process = ConsumerThread(consumer)
        self.process.start()
        self.process.join()

        self.assertEqual(consumer.logger.infos[0], 'Worker MainProcess ready')
        self.assertEqual(consumer.logger.errors[0], 'Received TERM Signal. Exiting MainProcess ...')

    @patch('rabbitpy.Queue', new=partial(MockQueue, content=[AttributeError('terminate')]))
    @patch('rabbitpy.Connection', MockConnection)
    def test_worker_exits_on_exception2_caused_by_TERM_signal(self):
        """
            Given a running worker
            When the consumer process raises an AttributeError triggered by a TERM signal
            Then the worker is forced to stop
        """
        runner = MockRunner('tests', 'maxbunny.ini', 'instances.ini')
        consumer = TestConsumer(runner)
        self.process = ConsumerThread(consumer)
        self.process.start()
        self.process.join()

        self.assertEqual(consumer.logger.infos[0], 'Worker MainProcess ready')
        self.assertEqual(consumer.logger.errors[0], 'Received TERM Signal. Exiting MainProcess ...')

    @patch('rabbitpy.Queue', new=partial(MockQueue, first=[AttributeError("'foo' object has no attribute 'bar'")]))
    @patch('rabbitpy.Connection', MockConnection)
    def test_worker_restarts_on_AttributeError_NOT_caused_by_TERM_signal(self):
        """
            Given a running worker
            When the consumer process raises an AttributeError NOt triggered by a TERM signal
            Then the worker is restarted
        """
        runner = MockRunner('tests', 'maxbunny.ini', 'instances.ini')
        consumer = TestConsumer(runner)
        self.process = ConsumerThread(consumer)
        self.process.start()
        self.process.join()

        self.assertEqual(consumer.logger.infos[0], 'Worker MainProcess ready')
        self.assertEqual(consumer.logger.infos[1], 'Worker MainProcess ready')
        self.assertEqual(consumer.logger.infos[2], 'Exiting Worker MainProcess')
        self.assertEqual(consumer.logger.warnings[0], "AttributeError: 'foo' object has no attribute 'bar'")
        self.assertEqual(consumer.logger.warnings[1], 'Restarting Worker MainProcess')

    @patch('rabbitpy.Queue', new=partial(MockQueue, content=[AssertionError('terminate')]))
    @patch('rabbitpy.Connection', MockConnection)
    def test_worker_exits_on_exception3_caused_by_TERM_signal(self):
        """
            Given a running worker
            When the consumer process raises an exception triggered by a TERM signal
            Then the worker is forced to stop
        """
        runner = MockRunner('tests', 'maxbunny.ini', 'instances.ini')
        consumer = TestConsumer(runner)
        self.process = ConsumerThread(consumer)
        self.process.start()
        self.process.join()

        self.assertEqual(consumer.logger.infos[0], 'Worker MainProcess ready')
        self.assertEqual(consumer.logger.errors[0], 'Received TERM Signal. Exiting MainProcess ...')


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
