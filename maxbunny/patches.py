import pkg_resources
import sys

# PATCH rabbitpy to modify client_properties to show
# maxbunny version info in Rabbitmq Management plugin

from pamqp import specification
from rabbitpy.channel0 import Channel0
import multiprocessing


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
        'consumer': multiprocessing.current_process().name,
        'library-version': pkg_resources.require('rabbitpy')[0].version
    }
    return specification.Connection.StartOk(client_properties=properties,
                                            response=self._credentials,
                                            locale=self._get_locale())


def patch_client_properties():
    Channel0._build_start_ok_frame = _build_start_ok_frame
