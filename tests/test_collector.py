import unittest
from collector.__main__ import safe_url, slug_for

class CollectorTests(unittest.TestCase):
    def test_https_allowlisted_url(self):
        self.assertEqual(safe_url("https://example.com/a", {"example.com"}), "https://example.com/a")
    def test_reject_http(self):
        with self.assertRaises(ValueError):
            safe_url("http://example.com/a", {"example.com"})
    def test_reject_unlisted_host(self):
        with self.assertRaises(ValueError):
            safe_url("https://evil.test/a", {"example.com"})
    def test_reject_url_credentials(self):
        with self.assertRaises(ValueError):
            safe_url("https://user:pass@example.com/a", {"example.com"})
    def test_stable_filename(self):
        self.assertEqual(slug_for("https://example.com/a"), slug_for("https://example.com/a"))

if __name__ == "__main__":
    unittest.main()
