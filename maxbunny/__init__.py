# -*- coding: utf-8 -*-

import ConfigParser
import argparse
import gevent
import logging
import signal
import sys

LOGGER = logging.getLogger('bunny')
BUNNY_NO_DOMAIN = 0x01

from maxbunny.runner import BunnyRunner
from maxbunny.utils import setup_logging

# PATCH Openssl to make it compatible with gevent
# This has to com previous to other patches as they reference OpenSSL too

from OpenSSL import *
from maxbunny.SSL import Connection

mod = __import__('OpenSSL').SSL
mod.Connection = Connection

from maxbunny.patches import patch_ssl_method
from maxbunny.patches import patch_client_properties

patch_ssl_method()
patch_client_properties()


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
