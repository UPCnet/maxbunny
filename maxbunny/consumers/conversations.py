# -*- coding: utf-8 -*-
from maxbunny import BUNNY_NO_DOMAIN
from maxbunny.consumer import BunnyConsumer, BunnyMessageCancel
from maxcarrot.message import RabbitMessage
from maxbunny.utils import extract_domain
import re
from StringIO import StringIO
import base64
import rabbitpy
import json


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
        domain = extract_domain(message)

        # determine message object type
        message_object_type = 'note'
        if 'image' in message.data:
            message_object_type = 'image'
        if 'file' in message.data:
            message_object_type = 'file'

        # Client will be None only if after determining the domain (or getting the default),
        # no client could be found matching that domain
        client = self.clients[domain]
        if client is None:
            raise BunnyMessageCancel('Unknown domain {}'.format(domain))

        username = message.get('user', {}).get('username', None)
        if username is None:
            raise BunnyMessageCancel('Missing username in message')
        endpoint = client.people[message.user['username']].conversations[conversation_id].messages

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

            activity = endpoint.post(**query)

        else:
            activity = endpoint.post(object_content=message.data.get('text'))

        #Activity post returned None, so user or conversation was not found
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
            "version": "4.0.3",
        })

        # include message activity id
        ack_message['data']['id'] = activity['id']

        if domain is not BUNNY_NO_DOMAIN:
            ack_message['domain'] = domain

        str_message = json.dumps(ack_message.packed)
        notification_message = rabbitpy.Message(self.channel, str_message)
        conversations_exchange = rabbitpy.Exchange(self.channel, '{}.publish'.format(message.user['username']), durable=True, exchange_type='topic')
        notification_message.publish(conversations_exchange, routing_key='{}.notifications'.format(conversation_id))


__consumer__ = ConversationsConsumer
