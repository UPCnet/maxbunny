# -*- coding: utf-8 -*-
from rabbitpy.exceptions import ConnectionResetException
from rabbitpy.exceptions import AMQPNotFound
from rabbitpy.exceptions import AMQPConnectionForced

from maxclient.rest import RequestError
from maxbunny.utils import get_message_uuid, send_requeue_traceback, send_drop_traceback
from maxcarrot.message import MaxCarrotParsingError

from logging.handlers import WatchedFileHandler

import logging
import multiprocessing
import rabbitpy
import re
import traceback
import time
import thread


class BunnyMessageRequeue(Exception):
    """
        To be raised when a message has to be requeued
    """


class BunnyMessageCancel(Exception):
    """
        To be raised when a message has to be canceled
    """
    def __init__(self, *args, **kwargs):
        self.notify = kwargs.pop('notify', True)
        super(BunnyMessageCancel, self).__init__(*args, **kwargs)


class BunnyConsumer(object):
    name = 'consumer'
    queue = 'amq.queue'

    def __init__(self, runner, workers):
        """
        """
        self.rabbitmq_server = runner.rabbitmq_server
        self.__configure__(runner)
        # Setup logger
        self.logger = self.configure_logger()
        self.root_logger = logging.getLogger('bunny')
        self.requeued = []
        self.workers = []
        self.channels = {}
        self.workers_count = workers
        self.debug = runner.debug

    def reset_connection(self):
        """
            Deletes the connection and channel of the current worker process
        """
        del self.channels[self.wid]

    @property
    def channel(self):
        """
            Opens a connection and a channel for each consumer process
            started
        """
        wrapper = self.channels.setdefault(self.wid, {})
        if 'connection' not in wrapper:
            wrapper['connection'] = rabbitpy.Connection(self.rabbitmq_server)

        if 'channel' not in wrapper:
            wrapper['channel'] = wrapper['connection'].channel()

        return wrapper['channel']

    @property
    def wid(self):
        """
            Returns the identifier of the current worker process
        """
        return multiprocessing.current_process().name

    def __configure__(self, runner):
        self.ready = runner.workers_ready
        self.mail_settings = {
            "server": runner.config.get('main', 'smtp_server'),
            "sender": runner.config.get('main', 'notify_address'),
            "recipients": runner.config.get('main', 'notify_recipients')
        }

        self.mail_settings['recipients'] = re.findall(r'[^\s,; ]+', self.mail_settings['recipients'])
        self.rabbitmq_server = runner.rabbitmq_server
        self.clients = runner.clients
        self.logging_folder = runner.config.get('main', 'logging_folder')

        # execute custom configuration options
        if hasattr(self, 'configure'):
            self.configure(runner)

    def configure_logger(self):
        logger = logging.getLogger(self.name)

        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(levelname)s %(asctime)s %(message)s')

        logname = self.logname if hasattr(self, 'logname') else '{}.log'.format(self.name)
        handler = WatchedFileHandler('{}/{}'.format(self.logging_folder, logname))
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)

        logger.addHandler(handler)

        return logger

    def start(self):
        """
            Spawn required workers for this consumer
        """
        for worker_id in range(self.workers_count):
            worker = multiprocessing.Process(
                name='consumers.{}.{}'.format(self.name, worker_id + 1),
                target=self.consume)
            self.workers.append(worker)
            worker.start()

    def stop_all(self):
        """
            Stops all consumer's workers_ready
        """
        for channel in self.channels:
            channel['connection'].close()

    def stop(self):
        """
            Stops the current process worker connection
        """
        self.logger.warning('Disconnecting worker {}'.format(self.wid))
        self.channels[self.wid]['connection'].close()

    def restart_worker(self, message):
        """
            Restarts a workers without exiting its process
        """
        self.root_logger.error(message)
        self.logger.warning('Exiting Worker {}'.format(self.wid))
        self.reset_connection()
        self.consume(nowait=True)

    def consume(self, nowait=False):
        """
            Start consuming loop for the current process.

            Loop tries to autorestart on any exception.
            Control+C causes worker to exit definitely.
        """
        restarted = False
        failed = False
        while not restarted:
            try:
                queue = rabbitpy.Queue(self.channel, self.queue)
            except Exception as exc:
                time.sleep(2)
                if not failed:
                    self.logger.info('Waiting for rabbitmq...')
                failed = True
            else:
                restarted = True

        if failed:
            self.logger.info('Connection with RabbitMQ recovered!')

        if not nowait:
            # Wait for all workers to start eating carrots
            self.ready.wait()

        self.logger.info('Worker {} ready'.format(self.wid))

        # Start consuming messages
        try:
            for message in queue.consume_messages():
                if message:
                    self.__process__(message)
        except KeyboardInterrupt:
            self.logger.warning('User Canceled')
            self.stop()
        except AMQPNotFound as exc:
            self.logger.warning('AMQPNotFound: {}'.format(exc.message.reply_text))
        except ConnectionResetException:
            self.restart_worker('Rabbit Connection Reset')
        except AMQPConnectionForced:
            self.restart_worker('Forced Connection Close')
        except thread.error:
            self.logger.error('TERM Signal Received. Dying ...')
        except AttributeError as exc:
            self.terminate(exc)
        except AssertionError as exc:
            self.terminate(exc)
        except Exception as exc:
            self.restart_worker('{}: {}'.format(exc.__class__, exc.message))

    def terminate(self, exc):
        """
            Evaluate if it's an exception caused by the TERM
            signal shutdown procedure.

            Restart worker if it's not.
        """
        failed_terminate = 'terminate' in exc.message
        failed_child_check = 'child process' in exc.message

        if failed_terminate or failed_child_check:
            self.logger.error('Received TERM Signal. Killing {} ...'.format(self.wid))
        else:
            self.restart_worker('{}: {}'.format(exc.__class__, exc.message))

    def ack(self, message):
        """
            Sends ack to rabbitmq for this message.
        """
        message.ack()

    def nack(self, message, error, notify=True):
        """
            Drops the message and sends nack to rabbitmq.
        """
        uuid = get_message_uuid(message)
        nouuid_error = ' (NO_UUID)' if not uuid else ''
        self.logger.warning('Message dropped{}, reason: {}'.format(nouuid_error, error))
        if uuid in self.requeued:
            self.requeued.remove(uuid)
        message.nack()

        error_log = traceback.format_exc()

        if notify:
            send_drop_traceback(
                self.mail_settings,
                self.name,
                error_log,
                message)

    def requeue(self, message, error):
        """
            Requeues messages with a uuid. Logs and notifies the first requeuing
            of each message to specified mail. Messages without uuid will be canceled
        """
        uuid = get_message_uuid(message)
        if uuid is None:
            self.nack(message, error.message)
        else:
            if uuid not in self.requeued:
                self.logger.warning('Message {} reueued, reason: {}'.format(uuid, error))
                error_log = traceback.format_exc()
                send_requeue_traceback(
                    self.mail_settings,
                    self.name,
                    error_log,
                    message)

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
            self.nack(message, error.message, notify=error.notify)

        except BunnyMessageRequeue as error:
            self.requeue(message, error.message)

        # Catch maxclient exceptions
        except RequestError as error:
            # Requeue messages on max server malfunction [5xx]
            if error.code / 100 == 5:
                error.message = 'Max server error: ' + error.message
                self.requeue(message, error)
            # Cancel message on any other error code
            else:
                error.message = 'Max server error: ' + error.message
                self.nack(message, error.message)
        except MaxCarrotParsingError:
            self.nack(message, 'MaxCarrot Parsing error')
        # Requeue messages on unknown consumer failures
        except Exception as error:
            error.message = 'Consumer failure: ' + error.message
            self.requeue(message, error)
        else:
            # If message successfull, remove it from requeued
            # (assuming it MAY have been requeued some time ago)
            # and acknowledge it
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
