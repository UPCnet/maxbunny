# The mocked MAX server assumes:

# A MAX server with a registered context at 'http://localhost:8081' with the
# Twitter hashtag 'thehashtag' and the registered user 'sunbit'. Two registered
# users: 'victor.fernandez' with the Twitter username 'sneridagh' and
# 'carles.bruguera' with the Twitter username 'sunbit'. The user
# 'victor.fernandez' is subscribed to the context.

from maxbunny.tests import RabbitpyMockMessage

BAD_MESSAGE = RabbitpyMockMessage({})

TWEETY_MESSAGE_FROM_CONTEXT = RabbitpyMockMessage({
    "a": "a", "o": "t", "s": "t", "v": 4.0, "g": "01234", "p": "2014-01-01T00:00:00",
    "d": {
        "stid": 000000000000000000,
        "message": "I Am a tweet from Twitter",
        "author": "twitter_context_user"
    }})

TWEETY_MESSAGE_FROM_USER = RabbitpyMockMessage({
    "a": "a", "o": "t", "s": "t", "v": 4.0, "g": "01234", "p": "2014-01-01T00:00:00",
    "d": {
        "stid": 000000000000000000,
        "message": "I Am a tweet from Twitter to #testing #thehashtag",
        "author": "twitter_user"
    }})


NO_CONTEXTS = [{}]
NO_USERS = [{}]

SINGLE_CONTEXT = [
    {
        ''
        'twitterHashtag': 'thehashtag',
        'url': 'http://tests.local/singlecontext',
        'twitterUsernameId': '5674472',
        'twitterUsername': 'twitter_context_user'
    }
]

SINGLE_USER = [
    {
        'username': 'max_user',
        'twitterUsername': 'twitter_user',
    }
]
