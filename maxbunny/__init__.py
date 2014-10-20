# -*- coding: utf-8 -*-

import ConfigParser
import argparse
import gevent
import logging
import signal
import sys
import pkg_resources

LOGGER = logging.getLogger('bunny')
BUNNY_NO_DOMAIN = 0x01

from maxbunny.runner import BunnyRunner
from maxbunny.utils import setup_logging

# PATCH Openssl to make it compatible with gevent

from OpenSSL import *
from maxbunny.SSL import Connection

mod = __import__('OpenSSL').SSL
mod.Connection = Connection


# PATCH rabbitpy to modify client_properties to show
# maxbunny version info in Rabbitmq Management plugin

from pamqp import specification
from rabbitpy.channel0 import Channel0


def _build_start_ok_frame(self):
    """Build and return the Connection.StartOk frame.

    :rtype: pamqp.specification.Connection.StartOk

    """
    properties = {
        'product': 'maxbunny',
        'platform': 'Python {0.major}.{0.minor}.{0.micro}'.format(sys.version_info),
        'capabilities': {'authentication_failure_close': True,
                         'basic.nack': True,
                         'connection.blocked': True,
                         'consumer_cancel_notify': True,
                         'publisher_confirms': True},
        'information': 'See http://rabbitpy.readthedocs.org',
        'version': pkg_resources.require('maxbunny')[0].version,
        'library': 'rabbitpy',
        'library-version': pkg_resources.require('rabbitpy')[0].version
    }
    return specification.Connection.StartOk(client_properties=properties,
                                            response=self._credentials,
                                            locale=self._get_locale())

Channel0._build_start_ok_frame = _build_start_ok_frame


def main(argv=sys.argv, quiet=False):  # pragma: no cover

    description = "Consumer for MAX RabbitMQ server queues."
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        '-c',
        '--config',
        dest='configfile',
        type=str,
        required=True,
        help=("Configuration file"))
    options = parser.parse_args()

    config = ConfigParser.ConfigParser()
    config.read(options.configfile)

    setup_logging(options.configfile)

    runner = BunnyRunner(config)
    runner.start()

    gevent.signal(signal.SIGQUIT, runner.quit)
    gevent.signal(signal.SIGINT, runner.quit)
    gevent.signal(signal.SIGABRT, runner.quit)
    gevent.signal(signal.SIGUSR1, runner.restart)

    gevent.wait()
    print 'EXIT'

if __name__ == '__main__':
    main()
