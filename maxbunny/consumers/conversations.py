# -*- coding: utf-8 -*-
from maxbunny.consumer import BUNNY_CANCEL
from maxbunny.consumer import BUNNY_OK
from maxbunny.consumer import BUNNY_REQUEUE
from maxbunny.consumer import BunnyConsumer

import time


class ConversationsConsumer(BunnyConsumer):
    """
    """
    name = 'conversations'
    queue = 'messages'

    def process(self, message):
        """
        """
        #print 'conversations', self.id, message.body
        if message.body in ['3', '6']:
            return BUNNY_REQUEUE
        if message.body == '0':
            return BUNNY_CANCEL

        if message.body == 'start':
            self.logger.info('start {}'.format(time.time()))
        if message.body == 'end':
            self.logger.info('end {}'.format(time.time()))
        return BUNNY_OK


__consumer__ = ConversationsConsumer
