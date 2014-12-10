class RabbitpyMockMessage(dict):
    def __init__(self, message):
        self.routing_key = message.pop('routing_key', '')
        self.update(message)

    def json(self):
        return dict(self)


BAD_MESSAGE = RabbitpyMockMessage({})
