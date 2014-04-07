from maxbunny.consumer import BunnyConsumer
from maxbunny.consumer import BUNNY_OK
from maxbunny.consumer import BUNNY_CANCEL
from maxbunny.consumer import BUNNY_REQUEUE

from apnsclient import Session


class PushConsumer(BunnyConsumer):
    """
    """
    name = 'push'
    queue = 'push'

    def configure(self):
        self.ios_session = Session()

    def process(self, message):
        """
        """
        #print 'push', self.id, message.body
        if message.body in ['3', '6']:
            return BUNNY_REQUEUE
        if message.body == '0':
            return BUNNY_CANCEL
        return BUNNY_OK


__consumer__ = PushConsumer
