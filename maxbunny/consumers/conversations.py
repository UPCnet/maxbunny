from maxbunny.consumer import BunnyConsumer
from maxbunny.consumer import BUNNY_OK
from maxbunny.consumer import BUNNY_CANCEL
from maxbunny.consumer import BUNNY_REQUEUE
import time


class ConversationsConsumer(BunnyConsumer):
    """
    """
    queue = 'messages'

    def _process(self, message):
        """
        """
        #print __name__, self.id, message.body
        if message.body in ['3', '6']:
            return BUNNY_REQUEUE
        if message.body == '0':
            return BUNNY_CANCEL

        if message.body == 'start':
            print 'start', time.time()
        if message.body == 'end':
            print 'end', time.time()
        return BUNNY_OK


__consumer__ = ConversationsConsumer
