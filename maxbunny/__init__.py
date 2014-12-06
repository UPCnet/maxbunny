# -*- coding: utf-8 -*-
"""
MAXBunny Multi-Queue Consumer

Usage:
    maxbunny [-c <configfile> -d <debug-consumer>]

Options:
    -c <configfile>, --config <configfile>          Location of the main config file [default: config/maxbunny.ini]
    -d <debug-consumer>, --debug <debug-consumer>   Any of [tweety, push, conversations] to debug standalone without multiprocessing
"""

from docopt import docopt

import ConfigParser
import logging
import os
import sys
import signal

LOGGER = logging.getLogger('bunny')
BUNNY_NO_DOMAIN = 0x01

from maxbunny.runner import BunnyRunner
from maxbunny.utils import setup_logging
from maxbunny.patches import patch_client_properties
from maxbunny.patches import patch_ssl_method

patch_ssl_method()
patch_client_properties()


def main(argv=sys.argv, quiet=False):  # pragma: no cover
    arguments = docopt(__doc__, version='MAXBunny Multi-Queue Consumer')

    config = ConfigParser.SafeConfigParser({
        "smtp_server": "localhost",
        "notify_address": "noreply@{}".format(os.uname()[1]),
        "notify_recipients": []
    })

    configfile = os.path.realpath(arguments['--config'])
    config.read(configfile)
    setup_logging(configfile)

    runner = BunnyRunner(config)

    signal.signal(signal.SIGTERM, runner.stop)
    runner.start()

if __name__ == '__main__':
    main()
