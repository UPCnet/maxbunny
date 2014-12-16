from maxbunny.consumer import BunnyConsumer
from maxbunny.consumer import BunnyMessageCancel
from maxbunny.consumer import BunnyMessageRequeue
from maxbunny.tests import get_storing_logger
from maxbunny.tests import MaxBunnyTestCase
from maxbunny.tests import MockRunner
from maxbunny.tests import MockSMTP
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
        else:
            return None

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
            Given a message with no UUID field
            When the consumer loop processes the message
            And the message triggers a Cancel exception
            Then the message is dropped
            And a warning is logged
            And the channel remains Open
        """
        runner = MockRunner('tests', 'maxbunny.ini', 'instances.ini')
        consumer = TestConsumer(runner, exception=BunnyMessageCancel('Testing message drop', notify=False))
        self.process = ConsumerThread(consumer)

        self.server.send('', '{}', routing_key='tests')
        self.process.start()

        sleep(0.2)  # Leave a minimum time to message to reach rabbitmq
        queued = self.server.get_all('tests')

        # MUST import sent here to get current sent mails
        from maxbunny.tests import sent

        self.assertEqual(len(queued), 0)
        self.assertEqual(len(sent), 0)
        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 1)
        self.assertTrue(self.process.isAlive())
        self.assertEqual(consumer.logger.warnings[0], 'Message dropped (NO_UUID), reason: Testing message drop')

        self.server.management.force_close(consumer.remote())

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
        consumer = TestConsumer(runner, exception=BunnyMessageCancel('Testing message drop', notify=False))
        self.process = ConsumerThread(consumer)

        self.server.send('', '{"g": "0123456789"}', routing_key='tests')
        self.process.start()

        sleep(0.2)  # Leave a minimum time to message to reach rabbitmq
        queued = self.server.get_all('tests')

        # MUST import sent here to get current sent mails
        from maxbunny.tests import sent

        self.assertEqual(len(queued), 0)
        self.assertEqual(len(sent), 0)
        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 1)
        self.assertTrue(self.process.isAlive())
        self.assertEqual(consumer.logger.warnings[0], 'Message dropped, reason: Testing message drop')

        self.server.management.force_close(consumer.remote())

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
        consumer = TestConsumer(runner, exception=BunnyMessageCancel('Testing message drop', notify=True))
        self.process = ConsumerThread(consumer)

        self.server.send('', '{"g": "0123456789"}', routing_key='tests')
        self.process.start()

        sleep(0.2)  # Leave a minimum time to message to reach rabbitmq
        queued = self.server.get_all('tests')

        # MUST import sent here to get current sent mails
        from maxbunny.tests import sent

        self.assertEqual(len(queued), 0)
        self.assertEqual(len(sent), 1)
        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 1)
        self.assertTrue(self.process.isAlive())
        self.assertEqual(consumer.logger.warnings[0], 'Message dropped, reason: Testing message drop')

        self.server.management.force_close(consumer.remote())

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
        consumer = TestConsumer(runner, exception=BunnyMessageCancel('Testing message drop', notify=True))
        self.process = ConsumerThread(consumer)

        self.server.send('', '{"g": "0123456789"}', routing_key='tests')
        self.process.start()

        sleep(0.2)  # Leave a minimum time to message to reach rabbitmq
        queued = self.server.get_all('tests')

        # MUST import sent here to get current sent mails
        from maxbunny.tests import sent

        self.assertEqual(len(queued), 0)
        self.assertEqual(len(sent), 0)
        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 1)
        self.assertTrue(self.process.isAlive())
        self.assertEqual(consumer.logger.warnings[0], 'Message dropped, reason: Testing message drop')

        self.server.management.force_close(consumer.remote())

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
        consumer = TestConsumer(runner, exception=RequestError(401, 'Unauthorized'))
        self.process = ConsumerThread(consumer)

        self.server.send('', '{"g": "0123456789"}', routing_key='tests')
        self.process.start()

        sleep(0.2)  # Leave a minimum time to message to reach rabbitmq
        queued = self.server.get_all('tests')

        # MUST import sent here to get current sent mails
        from maxbunny.tests import sent

        self.assertEqual(len(queued), 0)
        self.assertEqual(len(sent), 1)
        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 1)
        self.assertTrue(self.process.isAlive())
        self.assertEqual(consumer.logger.warnings[0], 'Message dropped, reason: Max server error: Unauthorized')

        self.server.management.force_close(consumer.remote())

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
        consumer = TestConsumer(runner, exception=MaxCarrotParsingError())
        self.process = ConsumerThread(consumer)

        self.server.send('', '{"g": "0123456789"}', routing_key='tests')
        self.process.start()

        sleep(0.2)  # Leave a minimum time to message to reach rabbitmq
        queued = self.server.get_all('tests')

        # MUST import sent here to get current sent mails
        from maxbunny.tests import sent

        self.assertEqual(len(queued), 0)
        self.assertEqual(len(sent), 1)
        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 1)
        self.assertTrue(self.process.isAlive())
        self.assertEqual(consumer.logger.warnings[0], 'Message dropped, reason: MaxCarrot Parsing error')

        self.server.management.force_close(consumer.remote())

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
        consumer = TestConsumer(runner, exception=RequestError(500, 'Internal Server Error'))
        self.process = ConsumerThread(consumer)

        self.server.send('', '{"g": "0123456789"}', routing_key='tests')
        self.process.start()

        # MUST import sent here to get current sent mails
        from maxbunny.tests import sent

        sleep(0.2)  # Leave a minimum time to mail to be sent

        self.assertEqual(len(sent), 1)
        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 1)
        self.assertTrue(self.process.isAlive())
        self.assertEqual(consumer.logger.warnings[0], 'Message 0123456789 reueued, reason: Internal Server Error')

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
        """
        runner = MockRunner('tests', 'maxbunny.ini', 'instances.ini')
        consumer = TestConsumer(runner, exception=BunnyMessageRequeue('Test requeueing'))
        self.process = ConsumerThread(consumer)

        self.server.send('', '{"g": "0123456789"}', routing_key='tests')
        self.process.start()

        # MUST import sent here to get current sent mails
        from maxbunny.tests import sent

        sleep(0.2)  # Leave a minimum time to mail to be sent

        self.assertEqual(len(sent), 1)
        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 1)
        self.assertTrue(self.process.isAlive())
        self.assertEqual(consumer.logger.warnings[0], 'Message 0123456789 reueued, reason: Test requeueing')

        self.server.management.force_close(consumer.remote())

        sleep(0.2)  # Leave a minimum time to rabbitmq to release messages

        queued = self.server.get_all('tests')
        self.assertEqual(len(queued), 1)

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
        consumer = TestConsumer(runner, exception=Exception('Unknown exception'))
        self.process = ConsumerThread(consumer)

        self.server.send('', '{"g": "0123456789"}', routing_key='tests')
        self.process.start()

        # MUST import sent here to get current sent mails
        from maxbunny.tests import sent

        sleep(0.2)  # Leave a minimum time to mail to be sent

        self.assertEqual(len(sent), 1)
        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 1)
        self.assertTrue(self.process.isAlive())
        self.assertEqual(consumer.logger.warnings[0], 'Message 0123456789 reueued, reason: Unknown exception')

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
        self.assertEqual(len(consumer.logger.warnings), 1)
        self.assertFalse(self.process.isAlive())
        self.assertEqual(consumer.logger.warnings[0], 'CONNECTION_FORCED - Closed via management plugin')

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

        sleep(0.2)  # Leave a minimum time to message to reach rabbitmq
        queued = self.server.get_all('tests')

        # MUST import sent here to get current sent mails
        from maxbunny.tests import sent

        self.assertEqual(len(queued), 0)
        self.assertEqual(len(sent), 0)
        self.assertEqual(len(consumer.logger.infos), 1)
        self.assertEqual(len(consumer.logger.warnings), 0)
        self.assertTrue(self.process.isAlive())
        self.server.management.force_close(consumer.remote())
