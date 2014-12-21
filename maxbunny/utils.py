# -*- coding: utf-8 -*-
from logging.config import fileConfig
from maxcarrot.message import RabbitMessage
from maxbunny import BUNNY_NO_DOMAIN
import ConfigParser
import os
import re
import json
import logging
import smtplib
from email.mime.text import MIMEText

requeued = logging.getLogger('requeues')
dropped = logging.getLogger('dropped')

UNICODE_ACCEPTED_CHARS = u'áéíóúàèìòùïöüçñ'
FIND_HASHTAGS_REGEX = r'(\s|^)#{1}([\w\-\_\.%s]+)' % UNICODE_ACCEPTED_CHARS
REQUEUE_TEMPLATE = """
Hello,

this message is to inform that a message has been requed because a failure
on a MaxBunny consumer at "{server}". You'll receive this notification only once
for each message, but the message will remain qeued. Please fix it !

Message adressed to destination: "{routing_key}" containing:

{message}

failed on consumer "{consumer}" with the following traceback:

{traceback}

"""

DROP_TEMPLATE = """
Hello,

this message is to inform that a message has been droppedd because a failure
on a MaxBunny consumer at "{server}". This message is definitely dropped and
won't go anywhere unless you add it manually.

Message adressed to destination: "{routing_key}" containing:

{message}

failed on consumer "{consumer}" with the following traceback:

{traceback}

"""


def extract_domain(message):
    domain = message.get('domain', '')
    try:
        domain = domain.strip()
    except:
        return BUNNY_NO_DOMAIN

    domain = domain if domain else BUNNY_NO_DOMAIN
    return domain


def normalize_message(message):
    # Catch malformed users as a single string
    user = message.get('user', None)

    if isinstance(user, dict):
        message_username = user.get('username', "")
        message_display_name = user.get('displayname', message_username)
    elif isinstance(user, basestring):
        message_username = user
        message_display_name = user

    if user is not None:
        message['user'] = {"username": message_username, "displayname": message_display_name}
    return message


def send_traceback(mail_settings, consumer_name, traceback, rabbitpy_message, template='', logger=None, subject=''):
    try:
        message = json.dumps(RabbitMessage.unpack(rabbitpy_message.json()))
    except:
        message = rabbitpy_message.body

    routing_key = rabbitpy_message.routing_key if rabbitpy_message.routing_key else 'UNKNOWN'
    params = {
        'server': os.uname()[1],
        'routing_key': routing_key,
        'consumer': consumer_name,
        'message': message,
        'traceback': traceback
    }

    mail_body = template.format(**params)
    exception_header = '\n' + '=' * 80 + '\nREQUEUE EXCEPTION LOG\n\n'
    logger.debug(exception_header + mail_body)

    #Try to send the mail if recipients provided
    if mail_settings['recipients']:
        smtp = smtplib.SMTP(mail_settings['server'])
        msg = MIMEText(mail_body)
        msg['Subject'] = subject
        msg['From'] = mail_settings['sender']
        msg['To'] = ', '.join(mail_settings['recipients'])
        smtp.sendmail(mail_settings['sender'], mail_settings['recipients'], msg.as_string())


def send_requeue_traceback(*args):
    send_traceback(
        *args,
        template=REQUEUE_TEMPLATE,
        logger=requeued,
        subject='MaxBunny message REQUEUED')


def send_drop_traceback(*args):
    send_traceback(
        *args,
        template=DROP_TEMPLATE,
        logger=dropped,
        subject='MaxBunny message DROPPED')


def get_message_uuid(rabbitpy_message):
    try:
        message = rabbitpy_message.json()

    except:
        return None
    else:
        return message.get('g', None)


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
