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
