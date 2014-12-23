from maxbunny.tests import MaxBunnyTestCase
from maxbunny.tests.mock_http import http_mock_info
from maxbunny import BUNNY_NO_DOMAIN
from maxclient.rest import MaxClient

import httpretty
import os


class GeneralTests(MaxBunnyTestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_domain_extraction_missing(self):
        from maxbunny.utils import extract_domain
        domain = extract_domain({})
        self.assertEqual(domain, BUNNY_NO_DOMAIN)

    def test_domain_extraction_empty(self):
        from maxbunny.utils import extract_domain
        domain = extract_domain({'domain': ''})
        self.assertEqual(domain, BUNNY_NO_DOMAIN)

    def test_domain_extraction_empty2(self):
        from maxbunny.utils import extract_domain
        domain = extract_domain({'domain': '  '})
        self.assertEqual(domain, BUNNY_NO_DOMAIN)

    def test_domain_extraction_invalid_type(self):
        from maxbunny.utils import extract_domain
        with self.assertRaises(AttributeError):
            extract_domain(1)

    def test_domain_extraction_invalid_type2(self):
        from maxbunny.utils import extract_domain
        with self.assertRaises(AttributeError):
            extract_domain([])

    def test_domain_extraction_invalid_type3(self):
        from maxbunny.utils import extract_domain
        domain = extract_domain({'domain': None})
        self.assertEqual(domain, BUNNY_NO_DOMAIN)

    def test_domain_extraction(self):
        from maxbunny.utils import extract_domain
        domain = extract_domain({'domain': 'tests'})
        self.assertEqual(domain, 'tests')

    def test_domain_extraction_padded(self):
        from maxbunny.utils import extract_domain
        domain = extract_domain({'domain': ' tests '})
        self.assertEqual(domain, 'tests')

    def test_normalize_message_without_user(self):
        from maxbunny.utils import normalize_message

        message = {"object": "message"}
        message_normalized = normalize_message(message)
        self.assertNotIn('user', message_normalized)

    def test_normalize_message_user_plain(self):
        from maxbunny.utils import normalize_message

        message = {"user": "testuser1"}
        message_normalized = normalize_message(message)
        self.assertEqual(message_normalized['user']['username'], 'testuser1')
        self.assertEqual(message_normalized['user']['displayname'], 'testuser1')

    def test_normalize_message_user_without_displayname(self):
        from maxbunny.utils import normalize_message

        message = {"user": {"username": "testuser1"}}
        message_normalized = normalize_message(message)
        self.assertEqual(message_normalized['user']['username'], 'testuser1')
        self.assertEqual(message_normalized['user']['displayname'], 'testuser1')

    def test_normalize_message_user_with_displayname(self):
        from maxbunny.utils import normalize_message

        message = {"user": {"username": "testuser1", "displayname": "Test User 1"}}
        message_normalized = normalize_message(message)
        self.assertEqual(message_normalized['user']['username'], 'testuser1')
        self.assertEqual(message_normalized['user']['displayname'], 'Test User 1')

    @httpretty.activate
    def test_reload_clients_from_changed_file(self):
        from maxbunny.clients import MaxClientsWrapper
        from maxbunny.tests import TESTS_PATH

        http_mock_info()

        clients = MaxClientsWrapper(
            '{}/{}'.format(TESTS_PATH, 'instances.ini'),
            'default',
            debug=os.environ.get('debug', False),
            client_class=MaxClient
        )
        test_client = clients['tests2']
        self.assertEqual(test_client, None)

        # Simulate that the instances.ini file has been updated,
        # by pointing the clients instance to another file to another file
        clients.instances = '{}/{}'.format(TESTS_PATH, 'instances2.ini'),
        test_client = clients['tests2']
        self.assertIsInstance(test_client, MaxClient)
