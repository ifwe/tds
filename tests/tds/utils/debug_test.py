import unittest
import tds.utils.debug as debug


class TestDebug(unittest.TestCase):
    def test_no_exception(self):
        def f(a, b, c=3):
            return a + b + c

        self.assertEqual(debug(f)(1, b=2), f(1, b=2))

    def test_exception(self):
        def f(a, b, c=3):
            raise Exception("oops")

        self.assertRaises(Exception, debug(f), (1,), {'b': 2})
