
class RabbitpyMockMessage(dict):
    def __init__(self, message):
        self.routing_key = message.pop('routing_key', '')
        self.update(message)

    def json(self):
        return dict(self)


BAD_MESSAGE = RabbitpyMockMessage({})


class APNSMockResponse(object):
    def __init__(self, failed):
        self.failed = failed


class GCMMockResponse(object):
    def __init__(self, response):
        self.success = response.get('success', {})
        self.unavailable = response.get('unavailable', [])
        self.not_registered = response.get('not_registered', [])
        self.failed = response.get('failed', {})
