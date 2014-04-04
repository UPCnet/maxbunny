import gevent
from gevent.pool import Pool
from maxbunny.clients import MaxClientsWrapper
import ConfigParser
import re
import logging
import importlib
import rabbitpy

logger = logging.getLogger('bunny')


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
        self.channel = self.conn.channel()

        for plugin in self.plugins:
            try:
                module = importlib.import_module('maxbunny.consumers.{}'.format(plugin))
            except ImportError:
                logger.info('No plugin named "{}" found'.format(plugin))
                break
            except:
                logger.info('An error occurred trying to load plugin "{}"'.format(plugin))
                break

            try:
                klass = getattr(module, '__consumer__')
            except AttributeError:
                logger.info('No consumer defined in plugin "{}"'.format(plugin))
                break
            except:
                logger.info('An error occurred trying to load consumer from plugin "{}"'.format(plugin))
                break

            self.consumers[plugin] = {
                'instance': klass,
                'workers': []
            }
            logger.info('Plugin "{}" loaded'.format(plugin))

        self.pool = Pool(len(self.consumers) * self.workers)

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
        worker_id = 0
        for plugin_id, consumer in self.consumers.items():
            for worker in range(self.workers):
                print worker_id
                self.pool.spawn(consumer['instance'](self.channel, self.rabbitmq_server, self.clients).run, worker_id)
                worker_id += 1

        while True:
            gevent.sleep(0.01)

    def stop(self):
        for plugin_id, consumer in self.consumers.items():
            for worker in consumer['workers']:
                worker.kill()
