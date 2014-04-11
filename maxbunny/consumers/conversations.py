# -*- coding: utf-8 -*-
from maxbunny.consumer import BUNNY_NO_DOMAIN
from maxbunny.consumer import BunnyConsumer
from maxcarrot.message import RabbitMessage

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

        conversation_id = re.search(r'(\w+).messages', rabbitpy_message.routing_key).groups()[0]
        domain = message.get('domain', BUNNY_NO_DOMAIN)
        client = self.clients[domain]
        endpoint = client.people[message.user['username']].conversations[conversation_id].messages

        endpoint.post(object_content=message.data['text'])
        return


__consumer__ = ConversationsConsumer
