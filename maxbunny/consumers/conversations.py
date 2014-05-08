# -*- coding: utf-8 -*-
from maxbunny.consumer import BUNNY_NO_DOMAIN
from maxbunny.consumer import BunnyConsumer, BunnyMessageCancel
from maxcarrot.message import RabbitMessage

import re
from StringIO import StringIO
import base64


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
        username = message.get('user', {}).get('username', None)
        if username is None:
            raise BunnyMessageCancel('Missing username in message')
        endpoint = client.people[message.user['username']].conversations[conversation_id].messages

        # determine message object type
        message_object_type = 'note'
        if 'image' in message.data:
            message_object_type = 'image'
        if 'file' in message.data:
            message_object_type = 'file'

        if message_object_type in ['image', 'file']:
            binary_data = base64.b64decode(message.data.get(message_object_type))
            file_object = StringIO(binary_data)
            query = dict(
                object_objectType=message_object_type,
                upload_file=file_object
            )
            object_content = message.data.get('text', '')
            if object_content:
                query['object_content'] = object_content

            object_filename = message.data.get('filename', '')
            if object_filename:
                query['object_filename'] = object_filename

            endpoint.post(**query)

        else:
            endpoint.post(object_content=message.data.get('text'))
        return


__consumer__ = ConversationsConsumer
