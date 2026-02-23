#!/usr/bin/env python3
"""Tests for PR and issue management."""

import unittest
from unittest.mock import patch, MagicMock
import json
import os
import sys

# Add bin to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))

# Use dynamic import to avoid type checking issues
linecook_module = __import__("line-cook")


class TestPRManagement(unittest.TestCase):
    """Test PR management methods."""

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
    def test_build_gh_pr_command_create(
        self, mock_run: MagicMock, mock_subprocess: MagicMock
    ) -> None:
        """Test building gh pr create command."""
        mock_run.return_value = "[]"
        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        cmd = bot._build_gh_pr_command(
            "create", title="Test PR", body="Test body"
        )
        self.assertEqual(cmd[0], "gh")
        self.assertEqual(cmd[1], "pr")
        self.assertEqual(cmd[2], "create")
        self.assertIn("--title", cmd)
        self.assertIn("Test PR", cmd)

    @patch("subprocess.run")
    @patch.object(linecook_module, "run")
    def test_build_gh_issue_command_create(
        self, mock_run: MagicMock, mock_subprocess: MagicMock
    ) -> None:
        """Test building gh issue create command."""
        mock_run.return_value = "[]"
        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        cmd = bot._build_gh_issue_command(
            "create", title="Test Issue", body="Test body"
        )
        self.assertEqual(cmd[0], "gh")
        self.assertEqual(cmd[1], "issue")
        self.assertEqual(cmd[2], "create")
        self.assertIn("--title", cmd)
        self.assertIn("Test Issue", cmd)

    @patch("subprocess.run")
    @patch.object(linecook_module, "run")
    def test_existing_sync_pr_found(
        self, mock_run: MagicMock, mock_subprocess: MagicMock
    ) -> None:
        """Test finding existing sync PR."""
        pr_data = [
            {
                "number": 123,
                "headRefName": "line-cook/fb_/update",
                "labels": [{"name": "line-cook"}],
            }
        ]
        mock_run.return_value = json.dumps(pr_data)

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        upstream_config = bot.upstreams["fb"]
        pr = bot.existing_sync_pr(upstream_config)
        self.assertIsNotNone(pr)
        self.assertEqual(pr["number"], 123)

    @patch("subprocess.run")
    @patch.object(linecook_module, "run")
    def test_existing_sync_pr_not_found(
        self, mock_run: MagicMock, mock_subprocess: MagicMock
    ) -> None:
        """Test when no existing sync PR is found."""
        mock_run.return_value = "[]"

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        upstream_config = bot.upstreams["fb"]
        pr = bot.existing_sync_pr(upstream_config)
        self.assertIsNone(pr)

    @patch("subprocess.run")
    @patch.object(linecook_module, "run")
    def test_bot_created_pr_closed_true(
        self, mock_run: MagicMock, mock_subprocess: MagicMock
    ) -> None:
        """Test detecting bot-created PR close event."""
        mock_run.return_value = "[]"
        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)
                bot.github_event_name = "pull_request_target"

        event = {
            "action": "closed",
            "pull_request": {
                "labels": [{"name": "line-cook"}, {"name": "other"}]
            },
        }

        result = bot.bot_created_pr_or_issue_closed(event)
        self.assertTrue(result)

    @patch("subprocess.run")
    @patch.object(linecook_module, "run")
    def test_bot_created_pr_closed_false(
        self, mock_run: MagicMock, mock_subprocess: MagicMock
    ) -> None:
        """Test non-bot PR close event."""
        mock_run.return_value = "[]"
        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)
                bot.github_event_name = "pull_request_target"

        event = {
            "action": "closed",
            "pull_request": {"labels": [{"name": "other"}]},
        }

        result = bot.bot_created_pr_or_issue_closed(event)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
