# -*- coding: utf-8 -*-
from logging.config import fileConfig
import ConfigParser
import os
import re

UNICODE_ACCEPTED_CHARS = u'áéíóúàèìòùïöüçñ'

FIND_HASHTAGS_REGEX = r'(\s|^)#{1}([\w\-\_\.%s]+)' % UNICODE_ACCEPTED_CHARS


def _getpathsec(config_uri, name):
    if '#' in config_uri:
        path, section = config_uri.split('#', 1)
    else:
        path, section = config_uri, 'main'
    if name:
        section = name
    return path, section


def setup_logging(config_uri):
    """
    Set up logging via the logging module's fileConfig function with the
    filename specified via ``config_uri`` (a string in the form
    ``filename#sectionname``).

    ConfigParser defaults are specified for the special ``__file__``
    and ``here`` variables, similar to PasteDeploy config loading.
    """
    path, _ = _getpathsec(config_uri, None)
    parser = ConfigParser.ConfigParser()
    parser.read([path])
    if parser.has_section('loggers'):
        config_file = os.path.abspath(path)
        return fileConfig(
            config_file,
            dict(__file__=config_file, here=os.path.dirname(config_file))
        )


def oauth2Header(username, token, scope="widgetcli"):
    return {
        "X-Oauth-Token": token,
        "X-Oauth-Username": username,
        "X-Oauth-Scope": scope}


def findHashtags(text):
    """
        Returns a list of valid #hastags in text
        Narrative description of the search pattern will be something like:
        "Any group of alphanumeric characters preceded by one (and only one) hash (#)
         At the begginning of a string or before a whitespace"

        teststring = "#first # Hello i'm a #text with #hashtags but#some are not valid#  # ##double #last"
        should return ['first', 'text', 'hashtags', 'last']
    """
    hashtags = [a.groups()[1] for a in re.finditer(FIND_HASHTAGS_REGEX, text)]
    lowercase = [hasht.lower() for hasht in hashtags]
    return lowercase
