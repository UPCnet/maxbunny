# -*- coding: utf-8 -*-
from maxbunny.consumer import BUNNY_CANCEL
from maxbunny.consumer import BUNNY_OK
from maxbunny.consumer import BUNNY_REQUEUE
from maxbunny.consumer import BunnyConsumer
from maxcarrot.message import RabbitMessage

from maxclient.rest import RequestError

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
        domain = message.get('domain', 'default')
        client = self.clients[domain]
        endpoint = client.people[message.user['username']].conversations[conversation_id].messages

        try:
            endpoint.post(object_content=message.data['text'])
        except RequestError as error:
            if error.code / 100 == 5:
                return BUNNY_REQUEUE
            else:
                return BUNNY_CANCEL
        else:
            return BUNNY_OK


__consumer__ = ConversationsConsumer
