# -*- coding: utf-8 -*-
from maxbunny.consumer import BUNNY_NO_DOMAIN
from maxbunny.consumer import BunnyConsumer
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
            endpoint.post(
                object_image_mimetype=message.data.get('mimetype', "image/jpeg"),
                object_objectType='image',
                object_content=message.data['text'],
                upload_file_image=file_object
            )
        else:
            endpoint.post(object_content=message.data['text'])
        return


__consumer__ = ConversationsConsumer
