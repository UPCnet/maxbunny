from maxbunny.tests.mockers import RabbitpyMockMessage

MISSING_USERNAME_MESSAGE = RabbitpyMockMessage({
    "routing_key": '0000000000000.messages',
    "s": "w", "v": 4.0, "g": "01234", "p": "2014-01-01T00:00:00",
    "a": "a", "o": "m",
    "d": {}
})

UNKNOWN_DOMAIN_MESSAGE = RabbitpyMockMessage({
    "routing_key": '0000000000000.messages',
    "s": "w", "v": 4.0, "g": "01234", "p": "2014-01-01T00:00:00",
    "a": "a", "o": "m",
    "u": {"u": "user1"}, "i": "unknown",
    "d": {}
})

MISSING_DOMAIN_MESSAGE = RabbitpyMockMessage({
    "routing_key": '0000000000000.messages',
    "s": "w", "v": 4.0, "g": "01234", "p": "2014-01-01T00:00:00",
    "a": "a", "o": "m",
    "u": {"u": "user1"},
    "d": {}
})

CONVERSATION_MESSAGE = RabbitpyMockMessage({
    "routing_key": '0000000000000.messages',
    "s": "w", "v": 4.0, "g": "01234", "p": "2014-01-01T00:00:00",
    "a": "a", "o": "m",
    "u": {"u": "user1"}, "i": "tests",
    "d": {}
})
