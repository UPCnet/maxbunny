from apnsclient import Session
from maxbunny.base import rabbitMQConsumer
from maxbunny.push import processPushMessage
from maxbunny.tweety import TweetyMessage
from maxbunny.utils import setup_logging

import argparse
import ConfigParser
import json
import logging
import os
import sys

LOGGER = logging.getLogger(__name__)


class MAXRabbitConsumer(rabbitMQConsumer):

    push_queue = 'push'
    tweety_queue = 'twitter'

    def __init__(self, config):
        self._connection = None
        self._channel = None
        self._closing = False
        self._push_consumer_tag = None
        self._tweety_consumer_tag = None
        self._url = 'amqp://guest:guest@{}:5672/%2F'.format(config.get('rabbitmq', 'server'))
        self.config = config
        self.ios_session = Session()

        self.load_settings()
        self.maxservers_settings = [maxserver for maxserver in self.config.sections() if maxserver.startswith('max_')]

    def on_channel_open(self, channel):
        LOGGER.info('Channel opened')
        self._channel = channel
        self.add_on_channel_close_callback()
        self.start_consuming()

    def start_consuming(self):
        LOGGER.info('Issuing consumer related RPC commands')
        self.add_on_cancel_callback()
        self._push_consumer_tag = self._channel.basic_consume(self.on_push_message,
                                                         self.push_queue)
        self._tweety_consumer_tag = self._channel.basic_consume(self.on_tweety_message,
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

        processPushMessage(self, body)

        self.acknowledge_message(basic_deliver.delivery_tag)

    def on_tweety_message(self, unused_channel, basic_deliver, properties, body):
        LOGGER.info('Received tweety message # %s from %s: %s',
                    basic_deliver.delivery_tag, properties.app_id, body)

        TweetyMessage(self, body).process()

        self.acknowledge_message(basic_deliver.delivery_tag)

    def load_settings(self):
        settings_file = '{}/.max_restricted'.format(self.config.get('max', 'config_directory'))
        if os.path.exists(settings_file):
            settings = json.loads(open(settings_file).read())
        else:
            settings = {}

        if 'token' not in settings or 'username' not in settings:
            LOGGER.info("Unable to load MAX settings, please execute RabbitMQ init script.")
            sys.exit(1)

        self.restricted_username = settings.get('username')
        self.restricted_token = settings.get('token')


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
