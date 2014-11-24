# -*- coding: utf-8 -*-
from maxbunny.clients import MaxClientsWrapper

import ConfigParser
import importlib
import logging
import os
import re
import multiprocessing


logger = logging.getLogger('bunny')


class BunnyRunner(object):

    def __init__(self, config):
        """
            Initialize and prepare plugin workers
        """
        self.config = config
        self.load_config(config)

        self.rabbitmq_server = self.common.get('rabbitmq', 'server')
        self.clients = MaxClientsWrapper(self.instances, self.config.get('main', 'default_domain'))

        self.consumers = {}
        self.workers_ready = multiprocessing.Event()

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
        instances_config_file = config.get('main', 'instances')

        self.common = ConfigParser.ConfigParser()
        self.common.read(common_config_file)

        self.cloudapis = ConfigParser.ConfigParser()
        self.cloudapis.read(cloudapis_config_file)

        self.instances = ConfigParser.ConfigParser()
        self.instances.read(instances_config_file)

    def start(self):
        """
            Start defined workers for each consumer
        """

        for consumer_id, consumer in self.consumers.items():
            consumer.start()

        self.workers_ready.set()

        try:
            for consumer_id, consumer in self.consumers.items():
                for worker in consumer.workers:
                    worker.join()
        except:
            logger.warning('MaxBunny exiting now...')
