import rabbitpy
import gevent
from gevent.hub import GreenletExit
from gevent.pool import Pool
from gevent import getcurrent
import logging

BUNNY_OK = 0x00
BUNNY_CANCEL = 0x01
BUNNY_REQUEUE = 0x02


class BunnyConsumer(object):
    name = 'consumer'
    queue = 'amq.queue'

    def __init__(self, channel, ready, rabbitmq_server, clients, workers, logging_folder):
        """
        """
        self.channel = channel
        self.ready = ready
        self.rabbitmq_server = rabbitmq_server
        self.clients = clients
        self.logging_folder = logging_folder

        # Setup logger
        self.logger = self.configure_logger()
        self.root_logger = logging.getLogger('bunny')

        self.pool = Pool(workers)

    def configure_logger(self):
        logger = logging.getLogger(self.name)

        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(levelname)s %(asctime)s %(message)s')

        handler = logging.FileHandler('{}/{}.log'.format(self.logging_folder, self.name))
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)

        logger.addHandler(handler)

        return logger

    def add_worker(self):
        self.pool.spawn(self.consume)

    def stop(self):
        self.pool.kill()

    def consume(self):
        """
            Start consuming loop
        """
        self.root_logger.info('Starting Worker {}'.format(id(getcurrent())))
        queue = rabbitpy.Queue(self.channel, self.queue)

        # Wait for all workers to start eating carrots
        self.ready.get()
        self.root_logger.info('Worker {} started'.format(id(getcurrent())))

        # Start consuming messages
        try:
            for message in queue.consume_messages():
                self.process(message)
                gevent.sleep()

        # Stop when required by runner
        except GreenletExit:
            self.root_logger.info('Exiting Worker {}'.format(id(getcurrent())))

    def process(self, message):
        """
            Common functionality for processing messages
            Processes the message and acks it
        """
        result = self._process(message)
        if result == BUNNY_OK:
            message.ack()
        elif result == BUNNY_CANCEL:
            message.nack()
        elif result == BUNNY_REQUEUE:
            message.nack(requeue=True)

    def _process(self, message):
        """
            Real processing code for consumers live here. Consumers implementing
            BunnyConsumer, receive a rabbitpy.Message and sould return one of
            BUNNY_OK, BUNNY_CANCEL or BUNNY_REQUEUE result codes
        """
        pass
