# -*- coding: utf-8 -*-
from gevent import getcurrent
from gevent.event import AsyncResult
from gevent.monkey import patch_all
from maxbunny.clients import MaxClientsWrapper

import ConfigParser
import gevent
import importlib
import logging
import rabbitpy
import re


logger = logging.getLogger('bunny')
patch_all()


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

        self.plugins = re.findall(r'\w+', self.config.get('main', 'plugins'))
        self.workers = int(self.config.get('main', 'workers'))

        self.conn = rabbitpy.Connection(self.rabbitmq_server)
        self.workers_ready = AsyncResult()

        for plugin in self.plugins:

            # Import consumer module, ignore it on errors
            try:
                module = importlib.import_module('maxbunny.consumers.{}'.format(plugin))
            except ImportError:
                logger.info('No plugin named "{}" found'.format(plugin))
                break
            except:
                logger.info('An error occurred trying to load plugin "{}"'.format(plugin))
                break

            # Load consumer class, ignore it on errors
            try:
                consumer_class = getattr(module, '__consumer__')
            except AttributeError:
                logger.info('No consumer defined in plugin "{}"'.format(plugin))
                break
            except:
                logger.info('An error occurred trying to load consumer from plugin "{}"'.format(plugin))
                break

            # Create a consumer instance for each plugin

            self.consumers[plugin] = consumer_class(self)
            logger.info('Plugin "{}" loaded'.format(plugin))

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

    def start_consumer(self, consumer):
        """
            Start a consumer with N workers for each plugin defined
        """
        for worker in range(self.workers):
            consumer.add_worker()
            gevent.sleep(ref=False)

    def restart(self, clean_restart=True, source=None):
        """
            Make sure all defined cosumers stop all spawned greenlets
            And try to reconnect to RabbitMQ. Once done, reinitialize
            consumers and restart the listening loops;
        """
        for plugin_id, consumer in self.consumers.items():
            if clean_restart:
                consumer.stop(ignore=source)
            consumer.empty_pool()
        restarted = False
        logger.info('Waiting for RabbitMQ ...')

        while not restarted:
            try:
                self.conn = rabbitpy.Connection(self.rabbitmq_server)
            except:
                gevent.sleep(2, ref=False)
                logger.info('Still waiting ...')
            else:
                restarted = True
                logger.info('Connection with RabbitMQ recovered!')
                self.workers_ready = AsyncResult()
                for plugin_id, consumer in self.consumers.items():
                    consumer.__configure__(self)
                self.start()

    def start(self):
        """
            Spawn as much workers as defined in maxbunny.ini config for each loaded plugin
        """
        for plugin_id, consumer in self.consumers.items():
            self.start_consumer(consumer)

        self.workers_ready.set(True)

    def stop(self):
        """
            Stop all consumers and close rabbitmq connection
        """
        logger.info("Stopping workers")
        for plugin_id, consumer in self.consumers.items():
            consumer.stop()
        logger.info("Disconnecting from rabbitmq")
        self.conn.close()

    def quit(self):
        """
            Final cleanup to exit process
        """
        self.stop()
        for plugin_id, consumer in self.consumers.items():
            consumer.empty_pool()
        gevent.kill(getcurrent())
