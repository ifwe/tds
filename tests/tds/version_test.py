import unittest
import version


class TestVersion(unittest.TestCase):
    def test_version_exists(self):
        self.assertIsInstance(version.__version__, basestring)
