from apnsclient import Session
from maxbunny.base import rabbitMQConsumer
from maxbunny.push import PushMessage
from maxbunny.tweety import TweetyMessage
from maxbunny.utils import setup_logging
from maxclient import MaxClient

import argparse
import ConfigParser
import json
import logging
import os
import sys

LOGGER = logging.getLogger('bunny')


class MaxClientsWrapper(object):
    """
        Mimics a dict of maxclients, which tries to reload new-defined maxservers
        from disk config file if asked for a non-existant client
    """
    def __init__(self, instances_config_file):
        self.instances_config_file = instances_config_file
        self.maxclients = {}
        self.load_instances()

    def load_instances(self):
        """
            Loads instances.ini and parses all maxservers. For each maxserver
            a maxclient with key "max_xxxxxx" is stored on self.maxclients
        """
        self.instances = ConfigParser.ConfigParser()
        self.instances.read(self.instances_config_file)

        max_instances = [maxserver for maxserver in self.instances.sections() if maxserver.startswith('max_')]

        # Instantiate a maxclient for each maxserver
        for maxserver in max_instances:
            maxclient = MaxClient(url=self.instances.get(maxserver, 'server'), oauth_server=self.instances.get(maxserver, 'oauth_server'))
            maxclient.setActor(self.instances.get(maxserver, 'restricted_user'))
            maxclient.setToken(self.instances.get(maxserver, 'restricted_user_token'))
            self.maxclients[maxserver] = maxclient

    def __getitem__(self, key):
        """
            Retrieves a specific maxserver client. Returns None if not found
        """
        maxclient = self.maxclients.get(key, None)

        # If no maxclient found
        if maxclient is None:
            # reload maxservers from file and try it again
            self.load_instances()
            maxclient = self.maxclients.get(key, None)

        return maxclient


class MAXRabbitConsumer(rabbitMQConsumer):

    push_queue = 'push'
    tweety_queue = 'twitter'

    def __init__(self, config):
        self._connection = None
        self._channel = None
        self._closing = False
        self._push_consumer_tag = None
        self._tweety_consumer_tag = None
        self.config = config

        common_config_file = self.config.get('main', 'common')
        cloudapis_config_file = self.config.get('main', 'cloudapis')
        instances_config_file = self.config.get('main', 'instances')

        self.common = ConfigParser.ConfigParser()
        self.common.read(common_config_file)

        self.cloudapis = ConfigParser.ConfigParser()
        self.cloudapis.read(cloudapis_config_file)

        self._url = self.common.get('rabbitmq', 'server')

        self.ios_session = Session()
        self.maxclients = MaxClientsWrapper(instances_config_file)

    def on_channel_open(self, channel):
        LOGGER.info('Channel opened')
        self._channel = channel
        self.add_on_channel_close_callback()
        self.start_consuming()

    def start_consuming(self):
        LOGGER.info('Issuing consumer related RPC commands')
        self.add_on_cancel_callback()
        self._push_consumer_tag = self._channel.basic_consume(
            self.on_push_message,
            self.push_queue)
        self._tweety_consumer_tag = self._channel.basic_consume(
            self.on_tweety_message,
            self.tweety_queue)

    def stop_consuming(self):
        if self._channel:
            LOGGER.info('Sending a Basic.Cancel RPC command to RabbitMQ')
            self._channel.basic_cancel(self.on_cancel_push_ok, self._push_consumer_tag)
            # The last one closes the channel (see on_cancel_tweety_ok)
            self._channel.basic_cancel(self.on_cancel_tweety_ok, self._tweety_consumer_tag)

    def on_cancel_push_ok(self, unused_frame):
        LOGGER.info('RabbitMQ acknowledged the cancellation of the push queue consumer')

    def on_cancel_tweety_ok(self, unused_frame):
        LOGGER.info('RabbitMQ acknowledged the cancellation of the tweety queue consumer')
        self.close_channel()

    def acknowledge_message(self, delivery_tag):
        LOGGER.info('Acknowledging message %s', delivery_tag)
        self._channel.basic_ack(delivery_tag)

    def on_push_message(self, unused_channel, basic_deliver, properties, body):
        LOGGER.info('Received push message # %s from %s: %s',
                    basic_deliver.delivery_tag, properties.app_id, body)

        PushMessage(self, body).process()

        self.acknowledge_message(basic_deliver.delivery_tag)

    def on_tweety_message(self, unused_channel, basic_deliver, properties, body):
        LOGGER.info('Received tweety message # %s from %s: %s',
                    basic_deliver.delivery_tag, properties.app_id, body)

        TweetyMessage(self, body).process()

        self.acknowledge_message(basic_deliver.delivery_tag)


def main(argv=sys.argv, quiet=False):  # pragma: no cover
    description = "Consumer for MAX RabbitMQ server queues."
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('-c', '--config',
                      dest='configfile',
                      type=str,
                      required=True,
                      help=("Configuration file"))
    options = parser.parse_args()

    config = ConfigParser.ConfigParser()
    config.read(options.configfile)

    setup_logging(options.configfile)

    consumer = MAXRabbitConsumer(config)

    try:
        consumer.run()
    except KeyboardInterrupt:
        consumer.stop()


if __name__ == '__main__':
    main()
