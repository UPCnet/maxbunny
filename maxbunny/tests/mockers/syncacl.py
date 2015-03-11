from maxbunny.tests.mockers import RabbitpyMockMessage

TASKS_MESSAGE = RabbitpyMockMessage({
    "routing_key": '', "i": "tests",
    "s": "w", "v": 4.0, "g": "01234", "p": "2014-01-01T00:00:00",
    "a": "m", "o": "x",
    'u': {'u': 'testuser1'},
    "d": {
        "context": 'e6847aed3105e85ae603c56eb2790ce85e212997',
        "tasks": {
            "subscribe": True,
            "grant": ['read'],
            "revoke": ['write']
        }
    }
})

TASKS_MESSAGE_MISSING_USERNAME = RabbitpyMockMessage({
    "routing_key": '', "i": "tests",
    "s": "w", "v": 4.0, "g": "01234", "p": "2014-01-01T00:00:00",
    "a": "m", "o": "x",
    "d": {
        "context": 'e6847aed3105e85ae603c56eb2790ce85e212997',
        "tasks": {
            "subscribe": True,
            "grant": ['read'],
            "revoke": ['write']
        }
    }
})

TASKS_MESSAGE_MISSING_CONTEXT = RabbitpyMockMessage({
    "routing_key": '', "i": "tests",
    "s": "w", "v": 4.0, "g": "01234", "p": "2014-01-01T00:00:00",
    "a": "m", "o": "x",
    'u': {'u': 'testuser1'},
    "d": {
        "tasks": {
            "subscribe": True,
            "grant": ['read'],
            "revoke": ['write']
        }
    }
})

TASKS_MESSAGE_MISSING_TASKS = RabbitpyMockMessage({
    "routing_key": '', "i": "tests",
    "s": "w", "v": 4.0, "g": "01234", "p": "2014-01-01T00:00:00",
    "a": "m", "o": "x",
    'u': {'u': 'testuser1'},
    "d": {
        "context": 'e6847aed3105e85ae603c56eb2790ce85e212997',
    }
})
