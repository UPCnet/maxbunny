import httpretty
import json
import re


def http_mock_info():
    httpretty.register_uri(
        httpretty.GET, re.compile("http://tests.\w+/info"),
        body='{"max.oauth_server": "http://oauth.local"}',
        status=200,
        content_type="application/json"
    )


def http_mock_contexts(contexts, uri='tests.local'):
    httpretty.register_uri(
        httpretty.GET, "http://{}/contexts?limit=0&twitter_enabled=True".format(uri),
        body=json.dumps(contexts),
        status=200,
        content_type="application/json"
    )


def http_mock_users(users, uri='tests.local'):
    httpretty.register_uri(
        httpretty.GET, "http://{}/people?limit=0&twitter_enabled=True".format(uri),
        body=json.dumps(users),
        status=200,
        content_type="application/json"
    )


def http_mock_post_context_activity(uri='tests.local'):
    httpretty.register_uri(
        httpretty.POST, re.compile("http://{}/contexts/\w+/activities".format(uri)),
        body=json.dumps({}),
        status=200,
        content_type="application/json"
    )


def http_mock_post_user_activity(uri='tests.local'):
    httpretty.register_uri(
        httpretty.POST, re.compile("http://{}/people/\w+/activities".format(uri)),
        body=json.dumps({}),
        status=201,
        content_type="application/json"
    )


def http_mock_post_user_message(uri='tests.local', message_id='0', status=201):
    httpretty.register_uri(
        httpretty.POST, re.compile("http://{}/people/\w+/conversations/\w+/messages".format(uri)),
        body=json.dumps({'id': message_id}),
        status=status,
        content_type="application/json"
    )


def http_mock_get_conversation_tokens(tokens, uri='tests.local', status=200):
    httpretty.register_uri(
        httpretty.GET, re.compile("http://{}/conversations/\w+/tokens".format(uri)),
        body=json.dumps(tokens),
        status=status,
        content_type="application/json"
    )
