import inspect
import pkg_resources
import sys

# PATCH APNS Client to force TLS
# This is needed because we are forced to use apns-client 0.1.8, as newer versions
# need an adaptation to work with gevent. Current version of ansclient has an option
# to specify openssl method

from apnsclient.apns import Certificate


def marmoset_patch(func, s, r):
    source = inspect.getsource(func).replace(s, r)
    exec source in func.func_globals
    func.func_code = func.func_globals[func.__name__].func_code


def patch_ssl_method():
    marmoset_patch(Certificate.__init__, 'SSLv3_METHOD', 'TLSv1_METHOD')


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


def patch_client_properties():
    Channel0._build_start_ok_frame = _build_start_ok_frame
