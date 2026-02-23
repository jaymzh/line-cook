#!/usr/bin/env python3
"""Tests for git utility functions."""

import unittest
from unittest.mock import patch, MagicMock
import subprocess
import os
import sys

# Add bin to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))

# Use dynamic import to avoid type checking issues
linecook_module = __import__("line-cook")


class TestGitUtils(unittest.TestCase):
    """Test git utility functions."""

    @patch("subprocess.run")
    def test_run_success(self, mock_run: MagicMock) -> None:
        """Test run() with successful command."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = linecook_module.run(["echo", "test"])
        self.assertEqual(result, "output")

    @patch("subprocess.run")
    def test_run_failure(self, mock_run: MagicMock) -> None:
        """Test run() with failed command."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error message"
        mock_run.return_value = mock_result

        with self.assertRaises(RuntimeError):
            linecook_module.run(["false"])

    @patch("subprocess.run")
    def test_git_success(self, mock_run: MagicMock) -> None:
        """Test git() with successful command."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "git output\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = linecook_module.git("status")
        self.assertEqual(result, "git output")

    @patch("subprocess.run")
    def test_try_git_success(self, mock_run: MagicMock) -> None:
        """Test try_git() with successful command."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        success, stdout, stderr = linecook_module.try_git("status")
        self.assertTrue(success)
        self.assertEqual(stdout, "output")
        self.assertEqual(stderr, "")

    @patch("subprocess.run")
    def test_try_git_failure(self, mock_run: MagicMock) -> None:
        """Test try_git() with failed command."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error"
        mock_run.return_value = mock_result

        success, stdout, stderr = linecook_module.try_git("invalid")
        self.assertFalse(success)
        self.assertEqual(stderr, "error")


if __name__ == "__main__":
    unittest.main()
