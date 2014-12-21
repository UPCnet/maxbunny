from maxbunny.tests.mockers import RabbitpyMockMessage
from maxbunny.tests.mockers import APNSMockResponse

from collections import namedtuple

ConversationData = namedtuple('ConversationData', ['id', 'users'])

CONVERSATION_0 = ConversationData('000000000000', [
    {'u': 'testuser0', 'd': 'Test User 0'},  # This is the sender
    {'u': 'testuser1', 'd': 'Test User 1'},
    {'u': 'testuser2', 'd': 'Test User 2'},
    {'u': 'testuser2', 'd': 'Test User 2'}])

CONVERSATION_ACK = RabbitpyMockMessage({
    "routing_key": '{.id}.messages'.format(CONVERSATION_0),
    "s": "b", "v": 4.0, "g": "01234", "p": "2014-01-01T00:00:00",
    "a": "k", "o": "m",
    "u": CONVERSATION_0.users[0], "i": "tests",
    "d": {"text": 'Test message', "id": "000000000001"}
})

CONVERSATION_PUSHDEBUG_ACK = RabbitpyMockMessage({
    "routing_key": '{.id}.messages'.format(CONVERSATION_0),
    "s": "b", "v": 4.0, "g": "01234", "p": "2014-01-01T00:00:00",
    "a": "k", "o": "m",
    "u": CONVERSATION_0.users[0], "i": "tests",
    "d": {"text": 'Test message #pushdebug', "id": "000000000001"}
})

UNKNOWN_OBJECT_CONVERSATION_ACK = RabbitpyMockMessage({
    "routing_key": '{.id}.messages'.format(CONVERSATION_0),
    "s": "b", "v": 4.0, "g": "01234", "p": "2014-01-01T00:00:00",
    "a": "k", "o": "?",
    "u": CONVERSATION_0.users[0], "i": "tests",
    "d": {"text": 'Test message', "id": "000000000001"}
})

MISSING_USER_CONVERSATION_ACK = RabbitpyMockMessage({
    "routing_key": '{.id}.messages'.format(CONVERSATION_0),
    "s": "b", "v": 4.0, "g": "01234", "p": "2014-01-01T00:00:00",
    "a": "k", "o": "?",
    "d": {"text": 'Test message', "id": "000000000001"}
})

EMPTY_USER_CONVERSATION_ACK = RabbitpyMockMessage({
    "routing_key": '{.id}.messages'.format(CONVERSATION_0),
    "s": "b", "v": 4.0, "g": "01234", "p": "2014-01-01T00:00:00",
    "a": "k", "o": "?",
    "u": {}, "i": "tests",
    "d": {"text": 'Test message', "id": "000000000001"}
})

NOMATCH_ROUTING_KEY_CONVERSATION_ACK = RabbitpyMockMessage({
    "routing_key": '{.id}'.format(CONVERSATION_0),
    "s": "b", "v": 4.0, "g": "01234", "p": "2014-01-01T00:00:00",
    "a": "k", "o": "m",
    "u": CONVERSATION_0.users[0], "i": "tests",
    "d": {"text": 'Test message', "id": "000000000001"}
})

NOID_ROUTING_KEY_CONVERSATION_ACK = RabbitpyMockMessage({
    "routing_key": '.messages',
    "s": "b", "v": 4.0, "g": "01234", "p": "2014-01-01T00:00:00",
    "a": "k", "o": "m",
    "u": CONVERSATION_0.users[0], "i": "tests",
    "d": {"text": 'Test message', "id": "000000000001"}
})

UNKNOWN_DOMAIN_CONVERSATION_ACK = RabbitpyMockMessage({
    "routing_key": '{.id}.messages'.format(CONVERSATION_0),
    "s": "b", "v": 4.0, "g": "01234", "p": "2014-01-01T00:00:00",
    "a": "k", "o": "m",
    "u": CONVERSATION_0.users[0], "i": "unknown",
    "d": {"text": 'Test message', "id": "000000000001"}
})

CONVERSATION_ACK_SUCCESS = APNSMockResponse({})

CONVERSATION_ACK_SUCCESS_ONE_INVALID = APNSMockResponse({
    '0123456789abcdef000000000000000000000000000000000000000000000003': (8, 'Invalid Token')
})

CONVERSATION_ACK_SUCCESS_ALL_INVALID = APNSMockResponse({
    '0123456789abcdef000000000000000000000000000000000000000000000001': (8, 'Invalid Token'),
    '0123456789abcdef000000000000000000000000000000000000000000000002': (8, 'Invalid Token'),
    '0123456789abcdef000000000000000000000000000000000000000000000003': (8, 'Invalid Token')
})
IOS_TOKENS = [
    {
        "username": "testuser0",
        "platform": "iOS",
        "token": "0123456789abcdef000000000000000000000000000000000000000000000000"
    },
    {
        "username": "testuser1",
        "platform": "iOS",
        "token": "0123456789abcdef000000000000000000000000000000000000000000000001"
    },
    {
        "username": "testuser2",
        "platform": "iOS",
        "token": "0123456789abcdef000000000000000000000000000000000000000000000002"
    },
    {
        "username": "testuser3",
        "platform": "iOS",
        "token": "0123456789abcdef000000000000000000000000000000000000000000000003"
    },
]

IOS_TOKENS_ONE_SHARED = [
    {
        "username": "testuser1",
        "platform": "iOS",
        "token": "0123456789abcdef000000000000000000000000000000000000000000000001"
    },
    {
        "username": "testuser2",
        "platform": "iOS",
        "token": "0123456789abcdef000000000000000000000000000000000000000000000002"
    },
    {
        "username": "testuser3",
        "platform": "iOS",
        "token": "0123456789abcdef000000000000000000000000000000000000000000000002"  # This token is shared with testuser2
    },
]
