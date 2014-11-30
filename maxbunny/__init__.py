# -*- coding: utf-8 -*-

import ConfigParser
import argparse
import logging
import os
import sys
import signal

LOGGER = logging.getLogger('bunny')
BUNNY_NO_DOMAIN = 0x01

from maxbunny.runner import BunnyRunner
from maxbunny.utils import setup_logging
from maxbunny.patches import patch_client_properties

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

    config = ConfigParser.SafeConfigParser({
        "smtp_server": "localhost",
        "notify_address": "noreply@{}".format(os.uname()[1]),
        "notify_recipients": ""
    })

    config.read(options.configfile)

    setup_logging(options.configfile)

    runner = BunnyRunner(config)

    signal.signal(signal.SIGTERM, runner.stop)
    runner.start()

if __name__ == '__main__':
    main()
