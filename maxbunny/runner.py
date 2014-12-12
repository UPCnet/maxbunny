# -*- coding: utf-8 -*-
from maxbunny.clients import MaxClientsWrapper

import ConfigParser
import importlib
import logging
import re
import multiprocessing


logger = logging.getLogger('bunny')


class BunnyRunner(object):

    def __init__(self, config, debug=False):
        """
            Initialize and prepare plugin workers
        """
        self.config = config
        self.debug = debug
        self.load_config(config)

        self.rabbitmq_server = self.common.get('rabbitmq', 'server')
        self.clients = MaxClientsWrapper(self.instances_config_file, self.config.get('main', 'default_domain'))
        failed = self.clients.load_instances()
        for maxserver, error_message in failed:
            logger.error('Error loading maxclient for [{}]: {}'.format(maxserver, error_message))

        self.consumers = {}
        self.workers_ready = multiprocessing.Event()

        if self.debug:
            plugin_config = [(self.debug, 1)]
        else:
            plugin_config = re.findall(r'(\w+)(?::(\d+))?', self.config.get('main', 'plugins'))

        for plugin_id, workers in plugin_config:
            workers = int(workers) if workers else 1
            Consumer = self.get_consumer_class(plugin_id)
            if Consumer:
                self.consumers[plugin_id] = Consumer(self, workers)
                logger.info('Plugin "{}" loaded'.format(plugin_id))

    def get_consumer_class(self, plugin):
        """
            Returns the consumer module for a plugin name, Return nothing on errors
        """
        try:
            module = importlib.import_module('maxbunny.consumers.{}'.format(plugin))
        except ImportError:
            logger.info('No plugin named "{}" found'.format(plugin))
            return None
        except:
            logger.info('An error occurred trying to load plugin "{}"'.format(plugin))
            return None

        # Load consumer class, ignore it on errors
        try:
            consumer_class = getattr(module, '__consumer__')
        except AttributeError:
            logger.info('No consumer defined in plugin "{}"'.format(plugin))
            return None
        except:
            logger.info('An error occurred trying to load consumer from plugin "{}"'.format(plugin))
            return None

        # Create a consumer instance for each plugin
        return consumer_class

    def load_config(self, config):
        """
            Loads and parses configuration files
        """
        common_config_file = config.get('main', 'common')
        cloudapis_config_file = config.get('main', 'cloudapis')
        self.instances_config_file = config.get('main', 'instances')

        self.common = ConfigParser.ConfigParser()
        self.common.read(common_config_file)

        self.cloudapis = ConfigParser.ConfigParser()
        self.cloudapis.read(cloudapis_config_file)

    def start(self):
        """
            Start defined workers for each consumer
        """
        try:
            if self.debug:
                self.start_standalone()
            else:
                self.start_multiprocessing()
        except OSError:
            logger.error('MaxBunny exiting now, forced death of all children :( ...')
        # except Exception:
        #     logger.warning('MaxBunny exiting now...')

    def start_multiprocessing(self):
        """
            Start child processes for each consumer
        """

        for consumer_id, consumer in self.consumers.items():
            consumer.start()

        self.workers_ready.set()

        for consumer_id, consumer in self.consumers.items():
            for worker in consumer.workers:
                worker.join()

    def start_standalone(self):
        """
            Start a single blocking consumer in the current process.__class__
        """
        consumer = self.consumers[self.debug]
        consumer.consume(nowait=True)

    def stop(self, *args):
        """
            Stops all consumer workers
        """
        for consumer in self.consumers.values():
            for worker in consumer.workers:
                if worker.is_alive():
                    worker.terminate()
