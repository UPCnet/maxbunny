# -*- coding: utf-8 -*-
from maxbunny import BUNNY_NO_DOMAIN
from maxbunny.consumer import BunnyConsumer
from maxbunny.consumer import BunnyMessageCancel
from maxbunny.utils import extract_domain
from maxcarrot.message import RabbitMessage

import json
import pkg_resources
import rabbitpy
import re


class ConversationsConsumer(BunnyConsumer):
    """
    """
    name = 'conversations'
    queue = 'messages'

    def process(self, rabbitpy_message):
        """
        """
        message = RabbitMessage.unpack(rabbitpy_message.json())

        match = re.search(r'(\w+).messages', rabbitpy_message.routing_key)

        if match:
            conversation_id = match.groups()[0]
        else:
            raise BunnyMessageCancel('Conversation id missing on routing_key "{}"'.format(rabbitpy_message.routing_key))

        domain = extract_domain(message)
        client = self.get_domain_client(domain)

        username = message.get('user', {}).get('username', None)
        if username is None:
            raise BunnyMessageCancel('Missing username in message')
        endpoint = client.people[message.user['username']].conversations[conversation_id].messages

        activity = endpoint.post(object_content=message.data.get('text'))

        # Activity post returned None, so user or conversation was not found
        if activity is None:
            try:
                message = json.loads(client.last_response)['error_description']
            except:
                message = "User or conversation not found"
            raise BunnyMessageCancel(message)

        # if we reached here, message was succesfully delivered so notify it

        ack_message = RabbitMessage()
        ack_message.prepare()
        ack_message.update({
            "uuid": message.uuid,
            "data": message.data,
            "user": message.user,
            "published": message.published,
            "action": "ack",
            "object": "message",
            "source": "maxbunny",
            "version": pkg_resources.require('maxbunny')[0].version,
        })

        # include message activity id
        ack_message['data']['id'] = activity['id']

        # include domain if it's specified
        if domain is not BUNNY_NO_DOMAIN:
            ack_message['domain'] = domain

        str_message = json.dumps(ack_message.packed)
        notification_message = rabbitpy.Message(self.channel, str_message)
        conversations_exchange = rabbitpy.Exchange(self.channel, '{}.publish'.format(message.user['username']), durable=True, exchange_type='topic')
        notification_message.publish(conversations_exchange, routing_key='{}.notifications'.format(conversation_id))

__consumer__ = ConversationsConsumer
