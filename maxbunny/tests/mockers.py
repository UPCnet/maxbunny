from maxbunny.tests import RabbitpyMockMessage

BAD_MESSAGE = RabbitpyMockMessage({})

TWEETY_MESSAGE_FROM_CONTEXT = RabbitpyMockMessage({
    "a": "a", "o": "t", "s": "t", "v": 4.0, "g": "01234", "p": "2014-01-01T00:00:00",
    "d": {
        "stid": 0,
        "message": "I Am a tweet from Twitter",
        "author": "twitter_context_user"
    }})

TWEETY_MESSAGE_FROM_USER = RabbitpyMockMessage({
    "a": "a", "o": "t", "s": "t", "v": 4.0, "g": "01234", "p": "2014-01-01T00:00:00",
    "d": {
        "stid": 0,
        "message": "I Am a tweet from Twitter going to #testing #thehashtag",
        "author": "twitter_user"
    }})

TWEETY_MESSAGE_FROM_USER_DEBUG = RabbitpyMockMessage({
    "a": "a", "o": "t", "s": "t", "v": 4.0, "g": "01234", "p": "2014-01-01T00:00:00",
    "d": {
        "stid": 0,
        "message": "I Am a tweet from Twitter going to #debug",
        "author": "twitter_user"
    }})

TWEETY_MESSAGE_FROM_USER_TWO_SECONDARY_HASHTAGS = RabbitpyMockMessage({
    "a": "a", "o": "t", "s": "t", "v": 4.0, "g": "01234", "p": "2014-01-01T00:00:00",
    "d": {
        "stid": 0,
        "message": "I Am a tweet from Twitter going to #testing #thehashtag and to #theotherhashtag",
        "author": "twitter_user"
    }})

TWEETY_MESSAGE_FROM_USER_TWO_GLOBAL = RabbitpyMockMessage({
    "a": "a", "o": "t", "s": "t", "v": 4.0, "g": "01234", "p": "2014-01-01T00:00:00",
    "d": {
        "stid": 0,
        "message": "I Am a tweet from Twitter going to #testing #thehashtag and #testing2 #thehashtag",
        "author": "twitter_user"
    }})

NO_CONTEXTS = [{}]
NO_USERS = [{}]

SINGLE_CONTEXT = [
    {
        'twitterHashtag': 'thehashtag',
        'url': 'http://tests.local/singlecontext',
        'twitterUsernameId': '5674472',
        'twitterUsername': 'twitter_context_user'
    }
]

# Two contexts that are linked to the same twitter user and hashtag
SHARED_INFO_CONTEXTS = [
    {
        'twitterHashtag': 'thehashtag',
        'url': 'http://tests.local/singlecontext',
        'twitterUsernameId': '5674472',
        'twitterUsername': 'twitter_context_user'
    },
    {
        'twitterHashtag': 'thehashtag',
        'url': 'http://tests.local/singlecontext2',
        'twitterUsernameId': '5674472',
        'twitterUsername': 'twitter_context_user'
    }
]

# Two set of contexts for different max instances that share a twitter user
CONTEXTS_SHARED_MAX_1 = [
    {
        'twitterHashtag': 'thehashtag',
        'url': 'http://tests.local/singlecontext',
        'twitterUsernameId': '5674472',
        'twitterUsername': 'twitter_context_user'
    }]

CONTEXTS_SHARED_MAX_2 = [
    {
        'twitterHashtag': 'thehashtag',
        'url': 'http://tests.local2/singlecontext2',
        'twitterUsernameId': '5674472',
        'twitterUsername': 'twitter_context_user'
    }]

TWO_HASHTAG_CONTEXTS = [
    {
        'twitterHashtag': 'thehashtag',
        'url': 'http://tests.local/singlecontext',
    },
    {
        'twitterHashtag': 'theotherhashtag',
        'url': 'http://tests.local/singlecontext2',
    }
]

TWO_MIXED_CONTEXTS = [
    {
        'twitterHashtag': 'thehashtag',
        'url': 'http://tests.local/singlecontext',
    },
    {
        'twitterUsernameId': '5674472',
        'twitterUsername': 'twitter_user',
        'url': 'http://tests.local/singlecontext2',
    }
]
SINGLE_USER = [
    {
        'username': 'max_user',
        'twitterUsername': 'twitter_user',
    }
]

MIXED_USERS = [
    {
        'username': 'max_user',
        'twitterUsername': 'twitter_user',
    },
    {
        'username': 'max_user_context',
        'twitterUsername': 'twitter_context_user',
    }
]
