# -*- coding: utf-8 -*-
from maxbunny.utils import get_message_uuid
from maxbunny.utils import send_drop_traceback
from maxbunny.utils import send_requeue_traceback
from maxcarrot.message import MaxCarrotParsingError
from maxclient.rest import RequestError
from maxbunny import BUNNY_NO_DOMAIN
from logging.handlers import WatchedFileHandler
from rabbitpy.exceptions import AMQPConnectionForced
from rabbitpy.exceptions import AMQPNotFound
from rabbitpy.exceptions import ConnectionResetException

import logging
import multiprocessing
import rabbitpy
import re
import thread
import time
import traceback


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
    queue = 'default'

    def __init__(self, runner, workers=1):
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
        self.logger.warning(message)
        self.logger.warning('Restarting Worker {}'.format(self.wid))
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
            self.logger.warning('AMQPNotFound: {}'.format(str(exc.message)))
        except ConnectionResetException:
            self.restart_worker('Rabbit Connection Reset')
        except AMQPConnectionForced as exc:
            self.logger.error(exc.message)
        except thread.error:
            self.logger.error('Received TERM Signal. Exiting {} ...'.format(self.wid))
        except AttributeError as exc:
            self.terminate(exc)
        except AssertionError as exc:
            self.terminate(exc)
        except Exception as exc:
            self.restart_worker('{}: {}'.format(exc.__class__.__name__, exc.message))
        else:
            self.logger.info('Exiting Worker {}'.format(self.wid))

    def terminate(self, exc):
        """
            Evaluate if it's an exception caused by the TERM
            signal shutdown procedure.

            Restart worker if it's not.
        """
        failed_terminate = 'terminate' in exc.message
        failed_child_check = 'child process' in exc.message

        if failed_terminate or failed_child_check:
            self.logger.error('Received TERM Signal. Exiting {} ...'.format(self.wid))
        else:
            self.restart_worker('{}: {}'.format(exc.__class__.__name__, exc.message))

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

        # Comentado que no envie la notificacion por mail si el mensaje ha sido descartado
        # tiquet 1230432 comentan que con el log es suficiente
        # if notify:
        #     send_drop_traceback(
        #         self.mail_settings,
        #         self.name,
        #         error_log,
        #         message)

    def requeue(self, message, error_message):
        """
            Requeues messages with a uuid. Logs and notifies the first requeuing
            of each message to specified mail. Messages without uuid will be canceled
        """
        uuid = get_message_uuid(message)
        if uuid is None:
            self.nack(message, error_message)
        else:
            if uuid not in self.requeued:
                self.logger.warning('Message {} reueued, reason: {}'.format(uuid, error_message))
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
                self.requeue(message, error.message)
            # Cancel message on any other error code
            else:
                error.message = 'Max server error: ' + error.message
                self.nack(message, error.message)
        except MaxCarrotParsingError:
            self.nack(message, 'MaxCarrot Parsing error')
        # Requeue messages on unknown consumer failures
        except Exception as error:
            error.message = 'Consumer failure: ' + error.message
            self.requeue(message, error.message)
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
            BunnyConsumer, receive a rabbitpy.Message and sould raise:

                * BunnyMessageCancel('reason') if the message has to be dropped
                * BunnyMessageRequeue('reason') if the message has to be requeued

            Return None on successfull processing
        """
        pass  # pragma: no cover

    def get_domain_client(self, domain):
        """
            Returns a valid domain, raises BunnyMessageCancel on failure.

            If client is None it means that we could not load a client for the specified domain
            Then we have to assert if it's because:
              - the domain is missing, and we couldn't load the default
              - Or the client for that domain is not defined or no client could be found matching that domain
        """
        client = self.clients[domain]
        if client is None and domain is BUNNY_NO_DOMAIN:
            raise BunnyMessageCancel('Missing domain, and default could not be loaded'.format(domain))
        elif client is None and domain is not BUNNY_NO_DOMAIN:
            raise BunnyMessageCancel('Unknown domain "{}"'.format(domain))

        return client
