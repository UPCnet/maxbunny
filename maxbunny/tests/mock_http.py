import httpretty
import json
import re


def http_mock_info():
    httpretty.register_uri(
        httpretty.GET, "http://tests.local/info",
        body='{"max.oauth_server": "http://oauth.local"}',
        status=200,
        content_type="application/json"
    )


def http_mock_contexts(contexts):
    httpretty.register_uri(
        httpretty.GET, "http://tests.local/contexts?limit=0&twitter_enabled=True",
        body=json.dumps(contexts),
        status=200,
        content_type="application/json"
    )


def http_mock_users(users):
    httpretty.register_uri(
        httpretty.GET, "http://tests.local/people?limit=0&twitter_enabled=True",
        body=json.dumps(users),
        status=200,
        content_type="application/json"
    )


def http_mock_post_context_activity():
    httpretty.register_uri(
        httpretty.POST, re.compile("http://tests.local/contexts/\w+/activities"),
        body=json.dumps({}),
        status=200,
        content_type="application/json"
    )


def http_mock_post_user_activity():
    httpretty.register_uri(
        httpretty.POST, re.compile("http://tests.local/people/\w+/activities"),
        body=json.dumps({}),
        status=201,
        content_type="application/json"
    )
