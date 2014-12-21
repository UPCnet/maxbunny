from maxbunny.tests import MaxBunnyTestCase
from maxbunny import BUNNY_NO_DOMAIN


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
