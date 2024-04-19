#!/usr/bin/env python3

import os
import sys
import unittest
from io import BytesIO, StringIO
from unittest.mock import patch

def _is_windows():
    return sys.platform.lower().startswith('win')

class FakeStdOut:
    def __init__(self) -> None:
        self.buffer = BytesIO()

class FakeStdIn:
    def __init__(self, loaded_str):
        if isinstance(loaded_str, str):
            loaded_str = loaded_str.encode()
        self.buffer = BytesIO(loaded_str)

class CliTests(unittest.TestCase):
    def test_placeholder(self):
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
