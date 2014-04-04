import rabbitpy
import gevent

BUNNY_OK = 0x00
BUNNY_CANCEL = 0x01
BUNNY_REQUEUE = 0x02


class BunnyConsumer(object):
    queue = 'amq.queue'

    def __init__(self, channel, rabbitmq_server, clients):
        """
        """
        self.channel = channel
        self.rabbitmq_server = rabbitmq_server
        self.clients = clients

    def run(self, worker_id):
        """
            Start consuming loop
        """
        #print 'start', worker_id
        self.id = worker_id
        queue = rabbitpy.Queue(self.channel, self.queue)
        # Consume the message
        for message in queue.consume_messages():
            self.process(message)
            #print 'after message', worker_id
            gevent.sleep(0.0000000000001)
        gevent.sleep(0.0000000000001)

    def process(self, message):
        """
            Common functionality for processing messages
            Processes the message and acks it
        """
        result = self._process(message)
        if result == BUNNY_OK:
            message.ack()
        elif result == BUNNY_CANCEL:
            message.nack()
        elif result == BUNNY_REQUEUE:
            message.nack(requeue=True)

    def _process(self, message):
        """
            Real processing code for consumers live here. Consumers implementing
            BunnyConsumer, receive a rabbitpy.Message and sould return one of
            BUNNY_OK, BUNNY_CANCEL or BUNNY_REQUEUE result codes
        """
        pass
