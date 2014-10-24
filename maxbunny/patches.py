import pkg_resources
import sys
import OpenSSL

# PATCH APNS Client to force TLS
# This is needed because we are forced to use apns-client 0.1.8, as newer versions
# need an adaptation to work with gevent. Current version of ansclient has an option
# to specify openssl method

from apnsclient.apns import Certificate


def __init__(self, cert_string=None, cert_file=None, key_string=None, key_file=None, passphrase=None):
    """ Provider's certificate and private key.

        Your certificate will probably contain the private key. Open it
        with any text editor, it should be plain text (PEM format). The
        certificate is enclosed in ``BEGIN/END CERTIFICATE`` strings and
        private key is in ``BEGIN/END RSA PRIVATE KEY`` section. If you can
        not find the private key in your .pem file, then you should
        provide it with `key_string` or `key_file` argument.

        .. note::
            If your private key is secured by a passphrase, then `pyOpenSSL`
            will query it from `stdin`. If your application is not running in
            the interactive mode, then don't protect your private key with a
            passphrase or use `passphrase` argument. The latter option is
            probably a big mistake since you expose the passphrase in your
            source code.

        :Arguments:
            - `cert_string` (str): certificate in PEM format from string.
            - `cert_file` (str): certificate in PEM format from file.
            - `key_string` (str): private key in PEM format from string.
            - `key_file` (str): private key in PEM format from file.
            - `passphrase` (str): passphrase for your private key.
    """
    self._context = OpenSSL.SSL.Context(OpenSSL.SSL.TLSv1_METHOD)

    if cert_file:
        # we have to load certificate for equality check. there is no
        # other way to obtain certificate from context.
        with open(cert_file, 'rb') as fp:
            cert_string = fp.read()

    cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert_string)
    self._context.use_certificate(cert)

    if not key_string and not key_file:
        # OpenSSL is smart enought to locate private key in certificate
        args = [OpenSSL.crypto.FILETYPE_PEM, cert_string]
        if passphrase is not None:
            args.append(passphrase)

        pk = OpenSSL.crypto.load_privatekey(*args)
        self._context.use_privatekey(pk)
    elif key_file and not passphrase:
        self._context.use_privatekey_file(key_file, OpenSSL.crypto.FILETYPE_PEM)

    else:
        if key_file:
            # key file is provided with passphrase. context.use_privatekey_file
            # does not use passphrase, so we have to load the key file manually.
            with open(key_file, 'rb') as fp:
                key_string = fp.read()

        args = [OpenSSL.crypto.FILETYPE_PEM, key_string]
        if passphrase is not None:
            args.append(passphrase)

        pk = OpenSSL.crypto.load_privatekey(*args)
        self._context.use_privatekey(pk)

    # check if we are not passed some garbage
    self._context.check_privatekey()

    # used to compare certificates.
    self._equality = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)

Certificate.__init__ = __init__

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
