# -*- coding: utf-8 -*-
from gevent import getcurrent
from gevent.hub import GreenletExit
from gevent.pool import Pool
from rabbitpy.exceptions import ConnectionResetException
from rabbitpy.exceptions import AMQPNotFound
from maxclient.rest import RequestError
from maxbunny.utils import get_message_uuid, send_requeue_traceback

import gevent
import logging
import rabbitpy
import traceback

BUNNY_NO_DOMAIN = 0x01


class BunnyMessageRequeue(Exception):
    """
        To be raised when a message has to be requeued
    """


class BunnyMessageCancel(Exception):
    """
        To be raised when a message has to be canceled
    """


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
        self.requeued = []

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
        except AMQPNotFound as exc:
            self.logger.warning('Exiting Worker {}, {}'.format(id(getcurrent()), exc.message.reply_text))
            self.stop()
            self.empty_pool()
        except GreenletExit:
            self.logger.info('Exiting Worker {}'.format(id(getcurrent())))
            self.stop_consuming()
        except ConnectionResetException:
            self.root_logger.warning('Rabbit Connection Reset')
            self.logger.warning('Exiting Worker {}'.format(id(getcurrent())))
            self.restart()
#        except Exception as exc:
#            self.root_logger.error('Crashed by unknown exception')
#            self.logger.warning('Exiting Worker {}'.format(id(getcurrent())))
#            self.restart()

    def ack(self, message):
        message.ack()

    def nack(self, message, error, reason):
        uuid = get_message_uuid(message)
        self.logger.warning('Message {} droped, reason: {}'.format(uuid, reason + error.message))
        if uuid in self.requeued:
            self.requeued.remove(uuid)
        message.nack()

    def requeue(self, message, error, reason):
        """
            Requeues messages with a uuid. Logs and notifies the first requeuing
            of each message to specified mail. Messages without uuid will be canceled
        """
        uuid = get_message_uuid(message)
        if uuid is None:
            self.logger.warning('Cannot requeue message without UUID, canceling)')
            message.nack()
        else:
            if uuid not in self.requeued:
                self.logger.warning('Message {} reueued, reason: {}'.format(uuid, reason + error.message))
                error_log = traceback.format_exc()
                mail = send_requeue_traceback(
                    'carlesba@gmail.com',
                    self.name,
                    error_log,
                    message)
                print mail
                self.requeued.append(uuid)
            message.nack(requeue=True)

    def __process__(self, message):
        """
            Common functionality for processing messages
            Processes the message and acks it
        """
        try:
            self.process(message)
        except BunnyMessageCancel as error:
            self.nack(message, error.message)

        except BunnyMessageRequeue as error:
            self.requeue(message, error.message)

        # Catch maxclient exceptions
        except RequestError as error:
            # Requeue messages on max server malfunction [5xx]
            if error.code / 100 == 5:
                self.requeue(message, error, 'Max server error: ')
            # Cancel message on any other error code
            else:
                self.nack(message, error, 'Max server error: ')
        # Requeue messages on unknown consumer failures
        except Exception as error:
            self.requeue(message, error, 'Consumer failure: ',)
        else:
            # If message successfull, remove it from requeued
            # (assuming it MAY have been requeued some time ago)
            # and acknowledge it
            self.ack(message)
            uuid = get_message_uuid(message)
            if uuid in self.requeued:
                self.requeued.remove(uuid)

    def process(self, message):
        """
            Real processing code for consumers live here. Consumers implementing
            BunnyConsumer, receive a rabbitpy.Message and sould return one of
            BUNNY_OK, BUNNY_CANCEL or BUNNY_REQUEUE result codes
        """
        pass
