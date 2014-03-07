import unittest2
import version


class TestVersion(unittest2.TestCase):
    def test_version_exists(self):
        assert isinstance(version.__version__, basestring)
