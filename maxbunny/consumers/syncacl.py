# -*- coding: utf-8 -*-
from maxbunny.consumer import BunnyConsumer
from maxbunny.consumer import BunnyMessageCancel
from maxbunny.utils import extract_domain
from maxbunny.utils import normalize_message
from maxcarrot.message import RabbitMessage
from maxclient.rest import RequestError


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
            # If subscription fails, try to create the user. If the problem wasn't an existent user
            # the atter subscription retry will fail with original error.
            try:
                client.contexts[message_context].subscriptions.post(actor_username=message_username, actor_objectType='person')
            except RequestError:
                client.people.post(username=message_username)
                client.contexts[message_context].subscriptions.post(actor_username=message_username, actor_objectType='person')

            successed_tasks.append('subscribe')

        do_unsubscribe = message_tasks.get('unsubscribe', None) is not None
        if do_unsubscribe:
            client.contexts[message_context].subscriptions[message_username].delete()
            successed_tasks.append('unsubscribe')

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
