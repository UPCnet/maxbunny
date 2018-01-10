from maxbunny.tests.mockers import RabbitpyMockMessage
from maxbunny.tests.mockers import APNSMockResponse
from maxbunny.tests.mockers import GCMMockResponse
from maxbunny.tests.mockers import FCMNotificationMockResponse

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

CONVERSATION_CREATION_ACK = RabbitpyMockMessage({
    "routing_key": '{.id}.messages'.format(CONVERSATION_0),
    "s": "b", "v": 4.0, "g": "01234", "p": "2014-01-01T00:00:00",
    "a": "a", "o": "c",
    "u": CONVERSATION_0.users[0], "i": "tests",
    "d": {"text": 'Test message', "id": "000000000001"}
})

BAD_ID_CONVERSATION_CREATION_ACK = RabbitpyMockMessage({
    "routing_key": '.messages',
    "s": "b", "v": 4.0, "g": "01234", "p": "2014-01-01T00:00:00",
    "a": "a", "o": "c",
    "u": CONVERSATION_0.users[0], "i": "tests",
    "d": {"text": 'Test message', "id": "000000000001"}
})

ACTIVITY_ACK = RabbitpyMockMessage({
    "routing_key": '{.id}.messages'.format(CONVERSATION_0),
    "s": "b", "v": 4.0, "g": "01234", "p": "2014-01-01T00:00:00",
    "a": "a", "o": "a",
    "u": CONVERSATION_0.users[0], "i": "tests",
    "d": {"text": 'Test message', "id": "000000000001"}
})

BAD_ID_ACTIVITY_ACK = RabbitpyMockMessage({
    "routing_key": ''.format(CONVERSATION_0),
    "s": "b", "v": 4.0, "g": "01234", "p": "2014-01-01T00:00:00",
    "a": "a", "o": "a",
    "u": CONVERSATION_0.users[0], "i": "tests",
    "d": {"text": 'Test message', "id": "000000000001"}
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

FIREBASE_CONVERSATION_ACK_SUCCESS = FCMNotificationMockResponse({
    'success': '3',
})

CONVERSATION_ACK_SUCCESS_ONE_INVALID = APNSMockResponse({
    '0123456789abcdef000000000000000000000000000000000000000000000003': (8, 'Invalid Token')
})

FIREBASE_CONVERSATION_ACK_SUCCESS_ONE_INVALID = FCMNotificationMockResponse({
    'success': '2',
    'failure': '1',
})

CONVERSATION_ACK_SUCCESS_ALL_INVALID = APNSMockResponse({
    '0123456789abcdef000000000000000000000000000000000000000000000001': (8, 'Invalid Token'),
    '0123456789abcdef000000000000000000000000000000000000000000000002': (8, 'Invalid Token'),
    '0123456789abcdef000000000000000000000000000000000000000000000003': (8, 'Invalid Token')
})

FIREBASE_CONVERSATION_ACK_SUCCESS_ALL_INVALID = FCMNotificationMockResponse({
    'failure': '3',
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

ANDROID_ACK_SUCCESS = GCMMockResponse({
    'success': {
        "APA91bEAYeD30DGSgmtqbSDH68Et2cjShC7zDloVjVjM3gUVocCAk76Hw_OOEq0skInyh2yL0pwsQG9JZiOlTxihfrFX_FO_Nnihn4pD2F5NaguVLoyMIIk8k83ja7le6SW6ZCh0TZfCCOwRuIBddskb2t_qr-001": True,
        "APA91bEAYeD30DGSgmtqbSDH68Et2cjShC7zDloVjVjM3gUVocCAk76Hw_OOEq0skInyh2yL0pwsQG9JZiOlTxihfrFX_FO_Nnihn4pD2F5NaguVLoyMIIk8k83ja7le6SW6ZCh0TZfCCOwRuIBddskb2t_qr-002": True,
        "APA91bEAYeD30DGSgmtqbSDH68Et2cjShC7zDloVjVjM3gUVocCAk76Hw_OOEq0skInyh2yL0pwsQG9JZiOlTxihfrFX_FO_Nnihn4pD2F5NaguVLoyMIIk8k83ja7le6SW6ZCh0TZfCCOwRuIBddskb2t_qr-003": True
    }
})

FIREBASE_ACK_SUCCESS = FCMNotificationMockResponse({
    'success': '3',
})


ANDROID_ACK_SUCCESS_ONE_FAILED = GCMMockResponse({
    'success': {
        "APA91bEAYeD30DGSgmtqbSDH68Et2cjShC7zDloVjVjM3gUVocCAk76Hw_OOEq0skInyh2yL0pwsQG9JZiOlTxihfrFX_FO_Nnihn4pD2F5NaguVLoyMIIk8k83ja7le6SW6ZCh0TZfCCOwRuIBddskb2t_qr-001": True,
        "APA91bEAYeD30DGSgmtqbSDH68Et2cjShC7zDloVjVjM3gUVocCAk76Hw_OOEq0skInyh2yL0pwsQG9JZiOlTxihfrFX_FO_Nnihn4pD2F5NaguVLoyMIIk8k83ja7le6SW6ZCh0TZfCCOwRuIBddskb2t_qr-002": True,
    },
    'failed': {
        "APA91bEAYeD30DGSgmtqbSDH68Et2cjShC7zDloVjVjM3gUVocCAk76Hw_OOEq0skInyh2yL0pwsQG9JZiOlTxihfrFX_FO_Nnihn4pD2F5NaguVLoyMIIk8k83ja7le6SW6ZCh0TZfCCOwRuIBddskb2t_qr-003": 'Android error message'
    }
})

FIREBASE_ACK_SUCCESS_ONE_FAILED = FCMNotificationMockResponse({
    'success': '2',
    'failure': '1',
})

ANDROID_ACK_SUCCESS_ALL_FAILED_MIXED = GCMMockResponse({
    'unavailable': ["APA91bEAYeD30DGSgmtqbSDH68Et2cjShC7zDloVjVjM3gUVocCAk76Hw_OOEq0skInyh2yL0pwsQG9JZiOlTxihfrFX_FO_Nnihn4pD2F5NaguVLoyMIIk8k83ja7le6SW6ZCh0TZfCCOwRuIBddskb2t_qr-001"],
    'not_registered': ["APA91bEAYeD30DGSgmtqbSDH68Et2cjShC7zDloVjVjM3gUVocCAk76Hw_OOEq0skInyh2yL0pwsQG9JZiOlTxihfrFX_FO_Nnihn4pD2F5NaguVLoyMIIk8k83ja7le6SW6ZCh0TZfCCOwRuIBddskb2t_qr-002"],
    'failed': {
        "APA91bEAYeD30DGSgmtqbSDH68Et2cjShC7zDloVjVjM3gUVocCAk76Hw_OOEq0skInyh2yL0pwsQG9JZiOlTxihfrFX_FO_Nnihn4pD2F5NaguVLoyMIIk8k83ja7le6SW6ZCh0TZfCCOwRuIBddskb2t_qr-003": 'Android error message'
    }
})

FIREBASE_ACK_SUCCESS_ALL_FAILED_MIXED = FCMNotificationMockResponse({
    'failure': '3',
})

ANDROID_TOKENS = [
    {
        "username": "testuser0",
        "platform": "android",
        "token": "APA91bEAYeD30DGSgmtqbSDH68Et2cjShC7zDloVjVjM3gUVocCAk76Hw_OOEq0skInyh2yL0pwsQG9JZiOlTxihfrFX_FO_Nnihn4pD2F5NaguVLoyMIIk8k83ja7le6SW6ZCh0TZfCCOwRuIBddskb2t_qr-000"
    },
    {
        "username": "testuser1",
        "platform": "android",
        "token": "APA91bEAYeD30DGSgmtqbSDH68Et2cjShC7zDloVjVjM3gUVocCAk76Hw_OOEq0skInyh2yL0pwsQG9JZiOlTxihfrFX_FO_Nnihn4pD2F5NaguVLoyMIIk8k83ja7le6SW6ZCh0TZfCCOwRuIBddskb2t_qr-001"
    },
    {
        "username": "testuser2",
        "platform": "android",
        "token": "APA91bEAYeD30DGSgmtqbSDH68Et2cjShC7zDloVjVjM3gUVocCAk76Hw_OOEq0skInyh2yL0pwsQG9JZiOlTxihfrFX_FO_Nnihn4pD2F5NaguVLoyMIIk8k83ja7le6SW6ZCh0TZfCCOwRuIBddskb2t_qr-002"
    },
    {
        "username": "testuser3",
        "platform": "android",
        "token": "APA91bEAYeD30DGSgmtqbSDH68Et2cjShC7zDloVjVjM3gUVocCAk76Hw_OOEq0skInyh2yL0pwsQG9JZiOlTxihfrFX_FO_Nnihn4pD2F5NaguVLoyMIIk8k83ja7le6SW6ZCh0TZfCCOwRuIBddskb2t_qr-003"
    },
]
