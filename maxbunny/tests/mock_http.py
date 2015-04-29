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


def http_mock_revoke_subscription_permission(uri='tests.local', status_code=204):
    httpretty.register_uri(
        httpretty.DELETE, re.compile("http://{}/contexts/\w+/permissions/\w+/\w+".format(uri)),
        status=status_code,
    )


def http_mock_grant_subscription_permission(uri='tests.local', status_code=201):
    httpretty.register_uri(
        httpretty.PUT, re.compile("http://{}/contexts/\w+/permissions/\w+/\w+".format(uri)),
        status=status_code,
    )


def http_mock_subscribe_user(uri='tests.local', fail_response=None):
    responses = [httpretty.Response(
        body=json.dumps({}),
        status=201,
        content_type="application/json")]
    if fail_response:
        responses.insert(0, fail_response)

    httpretty.register_uri(
        httpretty.POST, re.compile("http://{}/people/\w+/subscriptions".format(uri)),
        responses=responses
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


def http_mock_get_context_tokens(tokens, uri='tests.local', status=200):
    httpretty.register_uri(
        httpretty.GET, re.compile("http://{}/contexts/\w+/tokens".format(uri)),
        body=json.dumps(tokens),
        status=status,
        content_type="application/json"
    )


def http_mock_post_create_user(uri='tests.local', status=201):
    httpretty.register_uri(
        httpretty.POST, "http://{}/people".format(uri),
        body=json.dumps({}),
        status=status,
        content_type="application/json"
    )

