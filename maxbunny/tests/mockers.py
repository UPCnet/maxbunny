# The mocked MAX server assumes:

# A MAX server with a registered context at 'http://localhost:8081' with the
# Twitter hashtag 'thehashtag' and the registered user 'sunbit'. Two registered
# users: 'victor.fernandez' with the Twitter username 'sneridagh' and
# 'carles.bruguera' with the Twitter username 'sunbit'. The user
# 'victor.fernandez' is subscribed to the context.

contexts = [
    {
        'twitterHashtag': 'thehashtag',
        'displayName': 'Defaultcontext',
        'tags': [
        ],
        'url': 'http://localhost',
        'twitterUsernameId': '5674472',
        'published': '2013-08-08T20: 00: 21Z',
        'owner': 'victor.fernandez',
        'hash': '8523ab8065a69338d5006c34310dc8d2c0179ebb',
        'twitterUsername': 'sunbit',
        'objectType': 'context',
        'creator': 'victor.fernandez',
        'id': '5203f8d79afac6baf6148ec6',
        'permissions': {
            'read': 'public',
            'write': 'public',
            'invite': 'public',
            'subscribe': 'public'
        }
    }
]

users = [
    {
        'username': 'carles.bruguera',
        'iosDevices': [
        ],
        'displayName': 'carles.bruguera',
        'talkingIn': [
        ],
        'creator': 'victor.fernandez',
        'androidDevices': [
        ],
        'following': [
        ],
        'subscribedTo': [
        ],
        'last_login': '2013-08-08T19:54:43Z',
        'published': '2013-08-08T19:54:43Z',
        'owner': 'victor.fernandez',
        'twitterUsername': 'sunbit',
        'id': '5203f7839afac6b98c662bb0',
        'objectType': 'person'
    },
    {
        'username': 'victor.fernandez',
        'iosDevices': [
        ],
        'displayName': 'victor.fernandez',
        'talkingIn': [
        ],
        'creator': 'victor.fernandez',
        'androidDevices': [
        ],
        'following': [
        ],
        'subscribedTo': [
            {
                'twitterHashtag': 'thecontag',
                'displayName': 'Defaultcontext',
                'url': 'http://localhost',
                'twitterUsernameId': '5674472',
                'hash': '8523ab8065a69338d5006c34310dc8d2c0179ebb',
                'twitterUsername': 'sunbit',
                'objectType': 'context',
                'permissions': [
                    'read',
                    'write',
                    'unsubscribe'
                ]
            }
        ],
        'last_login': '2013-08-08T19:54:33Z',
        'published': '2013-08-08T19:54:33Z',
        'owner': 'victor.fernandez',
        'twitterUsername': 'sneridagh',
        'id': '5203f7799afac6b98c662baf',
        'objectType': 'person'
    }
]

response_followed_user = {
    'generator': 'Twitter',
    'creator': 'victor.fernandez',
    'contexts': [
        {
            'twitterHashtag': 'thecontag',
            'displayName': 'Defaultcontext',
            'tags': [
            ],
            'url': 'http://localhost',
            'published': '2013-08-08T20:00:21Z',
            'twitterUsernameId': '5674472',
            'owner': 'victor.fernandez',
            'hash': '8523ab8065a69338d5006c34310dc8d2c0179ebb',
            'twitterUsername': 'sunbit',
            'permissions': {
                'read': 'public',
                'write': 'public',
                'invite': 'public',
                'subscribe': 'public'
            },
            'creator': 'victor.fernandez',
            'id': '5203f8d79afac6baf6148ec6',
            'objectType': 'context'
        }
    ],
    'object': {
        'content': 'Hellooooo',
        'keywords': [
            'hellooooo'
        ],
        'objectType': 'note'
    },
    'replies': [

    ],
    'actor': {
        'url': 'http://localhost',
        'hash': '8523ab8065a69338d5006c34310dc8d2c0179ebb',
        'displayName': 'Defaultcontext',
        'objectType': 'uri'
    },
    'commented': '2013-08-12T07:28:28Z',
    'verb': 'post',
    'published': '2013-08-12T07:28:28Z',
    'owner': 'victor.fernandez',
    'id': '52088e9c9afac60f419e1c36',
    'objectType': 'activity'
}

response_hashtag = {
    'generator': 'Twitter',
    'creator': 'victor.fernandez',
    'contexts': [
        {
            'twitterHashtag': 'thecontag',
            'displayName': 'Defaultcontext',
            'url': 'http://localhost',
            'twitterUsernameId': '5674472',
            'hash': '8523ab8065a69338d5006c34310dc8d2c0179ebb',
            'twitterUsername': 'sunbit',
            'objectType': 'context'
        }
    ],
    'object': {
        'content': 'Hellooooo#upc#thehashtag',
        'hashtags': [
            'upc',
            'thehashtag'
        ],
        'objectType': 'note'
    },
    'replies': [

    ],
    'actor': {
        'username': 'victor.fernandez',
        'displayName': 'victor.fernandez',
        'objectType': 'person'
    },
    'commented': '2013-08-12T08:18:40Z',
    'verb': 'post',
    'published': '2013-08-12T08:18:40Z',
    'owner': 'victor.fernandez',
    'id': '52089a609afac617554ed481',
    'objectType': 'activity'
}

user_tokens = [
    {
        'username': 'victor.fernandez',
        'platform': 'iOS',
        'token': 'eabb12cb160e381045ce598b9f94f728ef237cc0779feb4ff87e03fc3bdbcefd'
    }
]
