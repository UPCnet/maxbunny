# -*- coding: utf-8 -*-
from gevent import getcurrent
from gevent.hub import GreenletExit
from gevent.pool import Pool
from rabbitpy.exceptions import ConnectionResetException

import gevent
import logging
import rabbitpy


BUNNY_OK = 0x00
BUNNY_CANCEL = 0x01
BUNNY_REQUEUE = 0x02
BUNNY_NO_DOMAIN = 0x04


class BunnyConsumer(object):
    name = 'consumer'
    queue = 'amq.queue'

    def __init__(self, runner):
        """
        """
        self.__configure__(runner)

        # Setup logger
        self.logger = self.configure_logger()
        self.root_logger = logging.getLogger('bunny')

    def __configure__(self, runner):
        self.channel = runner.conn.channel()
        self.ready = runner.workers_ready
        self.on_restart = runner.restart
        self.rabbitmq_server = runner.rabbitmq_server
        self.clients = runner.clients
        self.logging_folder = runner.config.get('main', 'logging_folder')
        self.pool = Pool(runner.workers)

        # execute custom configuration options
        if hasattr(self, 'configure'):
            self.configure(runner)

    def configure_logger(self):
        logger = logging.getLogger(self.name)

        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(levelname)s %(asctime)s %(message)s')

        logname = self.logname if hasattr(self, 'logname') else '{}.log'.format(self.name)
        handler = logging.FileHandler('{}/{}'.format(self.logging_folder, logname))
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)

        logger.addHandler(handler)

        return logger

    def add_worker(self):
        """
            Create a new greenlet with the consume task
        """
        self.pool.spawn(self.consume)

    def stop_consuming(self):
        """
            Close the channel to make all consumer connections disappear
        """
        self.channel.close()

    def stop_workers(self, ignore):
        """
            Kill consumer greenlets
        """
        grenlets = [greenlet for greenlet in self.pool]
        for greenlet in grenlets:
            if ignore is None or ignore == id(greenlet):
                greenlet.kill()

    def empty_pool(self):
        """
            Remove greenlets from the pool and disable it
        """
        grenlets = [greenlet for greenlet in self.pool]
        for greenlet in grenlets:
            self.pool.discard(greenlet)
        self.pool = None

    def stop(self, ignore=None):
        """
            Stop all consumer-related structures
        """
        self.stop_consuming()
        self.stop_workers(ignore=ignore)

    def restart(self):
        """
            Signal the runner a restart event, to broadcast to the rest of consumers
        """
        self.on_restart(clean_restart=True, source=id(getcurrent()))

    def consume(self):
        """
            Start consuming loop
        """
        queue = rabbitpy.Queue(self.channel, self.queue)

        # Wait for all workers to start eating carrots
        self.ready.get()
        self.logger.info('Worker {} ready'.format(id(getcurrent())))

        # Start consuming messages
        try:
            for message in queue.consume_messages():
                if message:
                    self.__process__(message)
                gevent.sleep(ref=True)

        # Stop when required by runner
        except GreenletExit:
            self.logger.info('Exiting Worker {}'.format(id(getcurrent())))
            self.stop_consuming()
        except ConnectionResetException:
            self.root_logger.warning('Rabbit Connection Reset')
            self.logger.warning('Exiting Worker {}'.format(id(getcurrent())))
            self.restart()

    def __process__(self, message):
        """
            Common functionality for processing messages
            Processes the message and acks it
        """
        result = self.process(message)
        if result == BUNNY_OK:
            message.ack()
        elif result == BUNNY_CANCEL:
            self.logger.warning('Message droped')
            message.nack()
        elif result == BUNNY_REQUEUE:
            self.logger.warning('Message requeued')
            message.nack(requeue=True)

    def process(self, message):
        """
            Real processing code for consumers live here. Consumers implementing
            BunnyConsumer, receive a rabbitpy.Message and sould return one of
            BUNNY_OK, BUNNY_CANCEL or BUNNY_REQUEUE result codes
        """
        pass
