"""
Unit tests for KanoAI One-Click launcher utilities.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
import start_all


class TestLauncher(unittest.TestCase):
    def test_repo_root_detection(self):
        self.assertTrue(os.path.isdir(start_all.REPO_ROOT))
        self.assertTrue(os.path.isdir(start_all.DOCS_DIR))
        self.assertTrue(os.path.isfile(os.path.join(start_all.DOCS_DIR, "index.html")))

    @patch("socket.socket")
    def test_is_port_in_use_true(self, mock_socket):
        instance = mock_socket.return_value.__enter__.return_value
        instance.connect_ex.return_value = 0
        self.assertTrue(start_all.is_port_in_use(8000))

    @patch("socket.socket")
    def test_is_port_in_use_false(self, mock_socket):
        instance = mock_socket.return_value.__enter__.return_value
        instance.connect_ex.return_value = 111  # ECONNREFUSED
        self.assertFalse(start_all.is_port_in_use(9999))

    @patch("urllib.request.urlopen")
    def test_wait_for_url_success(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.getcode.return_value = 200
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        self.assertTrue(start_all.wait_for_url("http://localhost:8000/api/health", timeout=1.0))


if __name__ == "__main__":
    unittest.main()
