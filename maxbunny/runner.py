import gevent
from gevent.monkey import patch_time
from gevent.event import AsyncResult
from maxbunny.clients import MaxClientsWrapper
import ConfigParser
import re
import logging
import importlib
import rabbitpy


logger = logging.getLogger('bunny')
patch_time()


class BunnyRunner(object):

    def __init__(self, config):
        """
            Initialize and prepare plugin workers
        """
        self.config = config
        self.load_config(config)

        self.rabbitmq_server = self.common.get('rabbitmq', 'server')
        self.clients = MaxClientsWrapper(self.instances)

        self.consumers = {}

        self.plugins = re.findall(r'\w+', self.config.get('main', 'plugins'))
        self.workers = int(self.config.get('main', 'workers'))

        self.conn = rabbitpy.Connection(self.rabbitmq_server)

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
                klass = getattr(module, '__consumer__')
            except AttributeError:
                logger.info('No consumer defined in plugin "{}"'.format(plugin))
                break
            except:
                logger.info('An error occurred trying to load consumer from plugin "{}"'.format(plugin))
                break

            # Create a consumer instance for each plugin
            self.workers_ready = AsyncResult()
            self.consumers[plugin] = klass(self.conn.channel(), self.workers_ready, self.rabbitmq_server, self.clients, self.workers, self.config.get('main', 'logging_folder'))
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

    def start(self):
        """
            Spawn as much workers as defined in maxbunny.ini config for each loaded plugin
        """
        for plugin_id, consumer in self.consumers.items():
            for worker in range(self.workers):
                consumer.add_worker()
                gevent.sleep()

        self.workers_ready.set(True)

        while True:
            try:
                gevent.sleep()
            except KeyboardInterrupt:
                self.stop()
                break

    def stop(self):
        logger.info("Stopping workers")
        for plugin_id, consumer in self.consumers.items():
            consumer.stop()
        logger.info("Disconnecting from rabbitmq")
        self.conn.close()
