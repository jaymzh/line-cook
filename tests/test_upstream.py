#!/usr/bin/env python3
"""Tests for upstream detection and management."""

import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add bin to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))

# Use dynamic import to avoid type checking issues
linecook_module = __import__("line-cook")


class TestUpstreamDetection(unittest.TestCase):
    """Test upstream detection methods."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.config = {
            "bot_label": "line-cook",
            "split_label": "line-cook-pr-split",
            "bot_command_prefix": "#linecook",
            "upstream_overrides": {},
            "universe_upstreams": {},
        }

    @patch("subprocess.run")
    @patch.object(linecook_module, "run")
    def test_get_upstream_for_cookbook_fb(
        self, mock_run: MagicMock, mock_subprocess: MagicMock
    ) -> None:
        """Test upstream detection for fb_ cookbook."""
        mock_run.return_value = "[]"
        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        upstream = bot._get_upstream_for_cookbook("fb_apache")
        self.assertIsNotNone(upstream)
        self.assertEqual(upstream["prefix"], "fb")

    @patch("subprocess.run")
    @patch.object(linecook_module, "run")
    def test_get_upstream_for_cookbook_pd(
        self, mock_run: MagicMock, mock_subprocess: MagicMock
    ) -> None:
        """Test upstream detection for pd_ cookbook."""
        config = self.config.copy()
        config["universe_upstreams"] = {
            "pd": {"prefix": "pd", "repo_url": "test.git"}
        }
        mock_run.return_value = "[]"

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=config, dry_run=True)

        upstream = bot._get_upstream_for_cookbook("pd_something")
        self.assertIsNotNone(upstream)
        self.assertEqual(upstream["prefix"], "pd")

    @patch("subprocess.run")
    @patch.object(linecook_module, "run")
    def test_get_upstream_for_cookbook_unknown(
        self, mock_run: MagicMock, mock_subprocess: MagicMock
    ) -> None:
        """Test upstream detection for unknown cookbook."""
        mock_run.return_value = "[]"
        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        upstream = bot._get_upstream_for_cookbook("unknown_cookbook")
        self.assertIsNone(upstream)


class TestUpstreamSetup(unittest.TestCase):
    """Test upstream configuration setup."""

    @patch("subprocess.run")
    @patch.object(linecook_module, "run")
    def test_setup_upstreams_primary_only(
        self, mock_run: MagicMock, mock_subprocess: MagicMock
    ) -> None:
        """Test upstream setup with primary only."""
        config = {
            "bot_label": "line-cook",
            "split_label": "line-cook-pr-split",
            "bot_command_prefix": "#linecook",
            "upstream_overrides": {},
            "universe_upstreams": {},
        }
        mock_run.return_value = "[]"

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=config, dry_run=True)

        self.assertIn("fb", bot.upstreams)
        self.assertTrue(bot.upstreams["fb"]["is_primary"])
        self.assertEqual(bot.upstreams["fb"]["trailer_key"], "Upstream-Commit")

    @patch("subprocess.run")
    @patch.object(linecook_module, "run")
    def test_setup_upstreams_multiple(
        self, mock_run: MagicMock, mock_subprocess: MagicMock
    ) -> None:
        """Test upstream setup with multiple upstreams."""
        config = {
            "bot_label": "line-cook",
            "split_label": "line-cook-pr-split",
            "bot_command_prefix": "#linecook",
            "upstream_overrides": {},
            "universe_upstreams": {
                "pd": {"prefix": "pd", "repo_url": "test1.git"},
                "xyz": {"prefix": "xyz", "repo_url": "test2.git"},
            },
        }
        mock_run.return_value = "[]"

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=config, dry_run=True)

        self.assertEqual(len(bot.upstreams), 3)
        self.assertIn("fb", bot.upstreams)
        self.assertIn("pd", bot.upstreams)
        self.assertIn("xyz", bot.upstreams)

        # Check non-primary trailer keys
        self.assertEqual(
            bot.upstreams["pd"]["trailer_key"], "pd_Upstream-Commit"
        )
        self.assertEqual(
            bot.upstreams["xyz"]["trailer_key"], "xyz_Upstream-Commit"
        )


if __name__ == "__main__":
    unittest.main()
