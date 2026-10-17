from twisted.trial import unittest

import minerva


class TestInit(unittest.TestCase):
    """
    Tests for `minerva.__init__`.
    """
    def test_version(self):
        """
        minerva.__version__ exists, is a str, and has a "."
        """
        self.assertIsInstance(minerva.__version__, str)
        self.assertIn('.', minerva.__version__)
