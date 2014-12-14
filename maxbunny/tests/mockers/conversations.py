from maxbunny.tests.mockers import RabbitpyMockMessage
from collections import namedtuple

ConversationData = namedtuple('ConversationData', ['id', 'users'])

CONVERSATION_0 = ConversationData('000000000000', ['testuser1', 'testuser2'])

MISSING_USERNAME_MESSAGE = RabbitpyMockMessage({
    "routing_key": '{.id}.messages'.format(CONVERSATION_0),
    "s": "w", "v": 4.0, "g": "01234", "p": "2014-01-01T00:00:00",
    "a": "a", "o": "m",
    "d": {}
})

UNKNOWN_DOMAIN_MESSAGE = RabbitpyMockMessage({
    "routing_key": '{.id}.messages'.format(CONVERSATION_0),
    "s": "w", "v": 4.0, "g": "01234", "p": "2014-01-01T00:00:00",
    "a": "a", "o": "m",
    "u": {"u": CONVERSATION_0.users[0]}, "i": "unknown",
    "d": {}
})

MISSING_DOMAIN_MESSAGE = RabbitpyMockMessage({
    "routing_key": '{.id}.messages'.format(CONVERSATION_0),
    "s": "w", "v": 4.0, "g": "01234", "p": "2014-01-01T00:00:00",
    "a": "a", "o": "m",
    "u": {"u": CONVERSATION_0.users[0]},
    "d": {}
})

CONVERSATION_MESSAGE = RabbitpyMockMessage({
    "routing_key": '{.id}.messages'.format(CONVERSATION_0),
    "s": "w", "v": 4.0, "g": "01234", "p": "2014-01-01T00:00:00",
    "a": "a", "o": "m",
    "u": {"u": CONVERSATION_0.users[0]}, "i": "tests",
    "d": {}
})
