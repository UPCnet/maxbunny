# -*- coding: utf-8 -*-
from maxbunny.consumer import BunnyConsumer
from maxbunny.consumer import BunnyMessageCancel
from maxbunny.utils import extract_domain
from maxbunny.utils import normalize_message
from maxcarrot.message import RabbitMessage


class SyncACLConsumer(BunnyConsumer):
    """
    """
    name = 'syncacl'
    queue = 'syncacl'

    def process(self, rabbitpy_message):
        """
        """
        packed_message = rabbitpy_message.json()
        message = normalize_message(RabbitMessage.unpack(packed_message))

        message_data = message.get('data', {})
        message_context = message_data.get('context', None)
        message_tasks = message_data.get('tasks', None)

        message_user = message.get('user', {})
        message_username = message_user.get('username', None)

        if not message_username:
            raise BunnyMessageCancel('Missing or empty user data')

        if not message_context:
            raise BunnyMessageCancel('Missing or empty context url')

        if not message_tasks:
            raise BunnyMessageCancel('Missing or empty tasks')

        domain = extract_domain(message)
        client = self.get_domain_client(domain)

        successed_tasks = []

        do_subscribe = message_tasks.get('subscribe', None) is not None
        if do_subscribe:
            client.people[message_username].subscriptions.post(object_url=message_context)
            successed_tasks.append('subscribe')

        revokes = message_tasks.get('revoke', [])
        for permission in revokes:
            client.contexts[message_context].permissions[message_username][permission].delete()
            successed_tasks.append('-{}'.format(permission))

        grants = message_tasks.get('grant', [])
        for permission in grants:
            client.contexts[message_context].permissions[message_username][permission].put()
            successed_tasks.append('+{}'.format(permission))

        self.logger.info('[{}] SUCCEDED {} on {} for {}'.format(domain, ', '.join(successed_tasks), message_context, message_username))


__consumer__ = SyncACLConsumer
