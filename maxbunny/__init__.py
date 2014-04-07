# -*- coding: utf-8 -*-
from maxbunny.utils import setup_logging

import ConfigParser
import argparse
import gevent
import logging
import signal
import sys


LOGGER = logging.getLogger('bunny')


from maxbunny.runner import BunnyRunner


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
