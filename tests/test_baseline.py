#!/usr/bin/env python3
"""Tests for baseline detection and onboarding operations."""

import unittest
from unittest.mock import patch, MagicMock
import json
import os
import sys

# Add bin to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))

# Use dynamic import to avoid type checking issues
linecook_module = __import__("line-cook")


class TestDetectGlobalBaseline(unittest.TestCase):
    """Test detect_global_baseline method."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.config = {
            "bot_label": "line-cook",
            "split_label": "line-cook-pr-split",
            "bot_command_prefix": "#linecook",
            "upstream_overrides": {},
            "universe_upstreams": {},
        }
        self.upstream_config = {
            "prefix": "fb",
            "remote": "fb_upstream",
            "branch": "main",
            "trailer_key": "Upstream-Commit",
            "ignore_cookbooks": [],
        }

    @patch.object(linecook_module.LineCook, "find_baseline_for_cookbook")
    @patch.object(linecook_module.LineCook, "list_local_cookbooks")
    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_detect_baseline_single_cookbook(
        self,
        mock_run: MagicMock,
        mock_git: MagicMock,
        mock_list: MagicMock,
        mock_find: MagicMock,
    ) -> None:
        """Test baseline detection with single cookbook."""
        mock_run.return_value = "[]"
        mock_list.return_value = ["fb_apache"]
        mock_find.return_value = "abc1234567890"

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        baseline, missing = bot.detect_global_baseline(self.upstream_config)

        self.assertEqual(baseline, "abc1234567890")
        self.assertEqual(len(missing), 0)

    @patch.object(linecook_module.LineCook, "find_baseline_for_cookbook")
    @patch.object(linecook_module.LineCook, "list_local_cookbooks")
    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_detect_baseline_multiple_cookbooks(
        self,
        mock_run: MagicMock,
        mock_git: MagicMock,
        mock_list: MagicMock,
        mock_find: MagicMock,
    ) -> None:
        """Test baseline detection with multiple cookbooks."""
        mock_run.return_value = "[]"
        mock_list.return_value = ["fb_apache", "fb_mysql"]
        mock_find.side_effect = ["abc1234567890", "def4567890123"]
        mock_git.return_value = "abc1234567890"  # merge-base result

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        baseline, missing = bot.detect_global_baseline(self.upstream_config)

        self.assertEqual(baseline, "abc1234567890")
        self.assertEqual(len(missing), 0)
        # Should call merge-base
        mock_git.assert_called_once()

    @patch.object(linecook_module.LineCook, "find_baseline_for_cookbook")
    @patch.object(linecook_module.LineCook, "list_local_cookbooks")
    @patch.object(linecook_module, "run")
    def test_detect_baseline_with_missing(
        self,
        mock_run: MagicMock,
        mock_list: MagicMock,
        mock_find: MagicMock,
    ) -> None:
        """Test baseline detection with missing cookbooks."""
        mock_run.return_value = "[]"
        mock_list.return_value = ["fb_apache", "fb_custom"]
        mock_find.side_effect = ["abc1234567890", None]

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        baseline, missing = bot.detect_global_baseline(self.upstream_config)

        self.assertEqual(baseline, "abc1234567890")
        self.assertEqual(len(missing), 1)
        self.assertIn("fb_custom", missing)


class TestFindBaselineForCookbook(unittest.TestCase):
    """Test find_baseline_for_cookbook method."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.config = {
            "bot_label": "line-cook",
            "split_label": "line-cook-pr-split",
            "bot_command_prefix": "#linecook",
            "upstream_overrides": {},
            "universe_upstreams": {},
        }
        self.upstream_config = {
            "prefix": "fb",
            "remote": "fb_upstream",
            "branch": "main",
            "trailer_key": "Upstream-Commit",
            "ignore_cookbooks": [],
        }

    @patch.object(linecook_module, "try_git")
    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_find_baseline_match(
        self,
        mock_run: MagicMock,
        mock_git: MagicMock,
        mock_try_git: MagicMock,
    ) -> None:
        """Test finding baseline when match exists."""
        mock_run.return_value = "[]"
        mock_git.return_value = "commit1\ncommit2\ncommit3"
        # First two commits have differences, third matches
        mock_try_git.side_effect = [
            (False, "", ""),
            (False, "", ""),
            (True, "", ""),
        ]

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        result = bot.find_baseline_for_cookbook(
            "fb_apache", self.upstream_config
        )

        self.assertEqual(result, "commit1")  # Reversed, so first match

    @patch.object(linecook_module, "try_git")
    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_find_baseline_no_match(
        self,
        mock_run: MagicMock,
        mock_git: MagicMock,
        mock_try_git: MagicMock,
    ) -> None:
        """Test finding baseline when no match exists."""
        mock_run.return_value = "[]"
        mock_git.return_value = "commit1\ncommit2"
        # All commits have differences
        mock_try_git.side_effect = [(False, "", ""), (False, "", "")]

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        result = bot.find_baseline_for_cookbook(
            "fb_custom", self.upstream_config
        )

        self.assertIsNone(result)


class TestSyncCookbookToBaseline(unittest.TestCase):
    """Test sync_cookbook_to_baseline method."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.config = {
            "bot_label": "line-cook",
            "split_label": "line-cook-pr-split",
            "bot_command_prefix": "#linecook",
            "upstream_overrides": {},
            "universe_upstreams": {},
        }
        self.upstream_config = {
            "prefix": "fb",
            "remote": "fb_upstream",
            "trailer_key": "Upstream-Commit",
            "ignore_cookbooks": [],
        }

    @patch.object(linecook_module, "try_git")
    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_sync_cookbook_success(
        self,
        mock_run: MagicMock,
        mock_git: MagicMock,
        mock_try_git: MagicMock,
    ) -> None:
        """Test successful cookbook sync to baseline."""
        mock_run.return_value = "[]"
        mock_try_git.side_effect = [
            (True, "", ""),  # cat-file check
            (True, "", ""),  # rm
            (False, "", ""),  # diff --cached --quiet (changes exist)
        ]
        mock_git.return_value = ""

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        result = bot.sync_cookbook_to_baseline(
            "fb_apache", "abc1234567890", self.upstream_config
        )

        self.assertTrue(result)

    @patch.object(linecook_module, "try_git")
    @patch.object(linecook_module, "run")
    def test_sync_cookbook_not_in_upstream(
        self,
        mock_run: MagicMock,
        mock_try_git: MagicMock,
    ) -> None:
        """Test syncing cookbook that doesn't exist in upstream."""
        mock_run.return_value = "[]"
        mock_try_git.return_value = (False, "", "")  # cat-file fails

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        result = bot.sync_cookbook_to_baseline(
            "fb_custom", "abc1234567890", self.upstream_config
        )

        self.assertFalse(result)


class TestOnboardingPR(unittest.TestCase):
    """Test onboarding PR operations."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.config = {
            "bot_label": "line-cook",
            "split_label": "line-cook-pr-split",
            "bot_command_prefix": "#linecook",
            "upstream_overrides": {},
            "universe_upstreams": {},
        }

    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_existing_onboarding_pr_found(
        self, mock_run: MagicMock, mock_git: MagicMock
    ) -> None:
        """Test finding existing onboarding PR."""
        pr_data = [
            {
                "number": 50,
                "headRefName": "line-cook/fb_onboard",
                "labels": [{"name": "line-cook"}],
            }
        ]
        mock_run.return_value = json.dumps(pr_data)

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        result = bot.existing_onboarding_pr("fb")

        self.assertIsNotNone(result)
        self.assertEqual(result["number"], 50)

    @patch.object(linecook_module, "run")
    def test_existing_onboarding_pr_not_found(
        self, mock_run: MagicMock
    ) -> None:
        """Test when no onboarding PR exists."""
        mock_run.return_value = "[]"

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        result = bot.existing_onboarding_pr("fb")

        self.assertIsNone(result)

    @patch.object(linecook_module.LineCook, "existing_onboarding_pr")
    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_create_onboarding_pr_new(
        self,
        mock_run: MagicMock,
        mock_git: MagicMock,
        mock_existing: MagicMock,
    ) -> None:
        """Test creating new onboarding PR."""
        mock_run.return_value = "https://github.com/test/repo/pull/100"
        mock_existing.return_value = None
        mock_git.return_value = ""

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(
                    config=self.config, dry_run=False
                )

        result = bot.create_onboarding_pr(
            "abc1234567890", "Upstream-Commit", "fb"
        )

        self.assertEqual(result, 100)

    @patch.object(linecook_module.LineCook, "existing_onboarding_pr")
    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_create_onboarding_pr_update_existing(
        self,
        mock_run: MagicMock,
        mock_git: MagicMock,
        mock_existing: MagicMock,
    ) -> None:
        """Test updating existing onboarding PR."""
        mock_run.return_value = ""
        mock_existing.return_value = {"number": 50}
        mock_git.return_value = ""

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(
                    config=self.config, dry_run=False
                )

        result = bot.create_onboarding_pr(
            "abc1234567890", "Upstream-Commit", "fb"
        )

        self.assertEqual(result, 50)


class TestFixupPR(unittest.TestCase):
    """Test fixup PR operations."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.config = {
            "bot_label": "line-cook",
            "split_label": "line-cook-pr-split",
            "bot_command_prefix": "#linecook",
            "upstream_overrides": {},
            "universe_upstreams": {},
        }
        self.upstream_config = {
            "prefix": "fb",
            "remote": "fb_upstream",
            "trailer_key": "Upstream-Commit",
            "ignore_cookbooks": [],
        }

    @patch.object(linecook_module, "run")
    def test_existing_fixup_pr_found(self, mock_run: MagicMock) -> None:
        """Test finding existing fixup PR."""
        pr_data = [
            {
                "number": 60,
                "headRefName": "line-cook/fb_fix_missing_baselines",
                "labels": [],
            }
        ]
        mock_run.return_value = json.dumps(pr_data)

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        result = bot.existing_fixup_pr("fb")

        self.assertIsNotNone(result)
        self.assertEqual(result["number"], 60)

    @patch.object(linecook_module.LineCook, "existing_fixup_pr")
    @patch.object(linecook_module.LineCook, "sync_cookbook_to_baseline")
    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_create_fixup_pr_success(
        self,
        mock_run: MagicMock,
        mock_git: MagicMock,
        mock_sync: MagicMock,
        mock_existing: MagicMock,
    ) -> None:
        """Test creating fixup PR successfully."""
        mock_run.return_value = "https://github.com/test/repo/pull/61"
        mock_existing.return_value = None
        mock_sync.return_value = True
        mock_git.side_effect = [
            "",  # checkout -B
            "abc1234567890",  # rev-parse base_branch
            "def4567890123",  # rev-parse HEAD (different)
            "",  # push
        ]

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(
                    config=self.config, dry_run=False
                )

        result = bot.create_or_update_fixup_pr(
            ["fb_custom"], "baseline123", self.upstream_config
        )

        self.assertEqual(result, 61)
        mock_sync.assert_called_once()

    @patch.object(linecook_module.LineCook, "existing_fixup_pr")
    @patch.object(linecook_module.LineCook, "sync_cookbook_to_baseline")
    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_create_fixup_pr_no_changes(
        self,
        mock_run: MagicMock,
        mock_git: MagicMock,
        mock_sync: MagicMock,
        mock_existing: MagicMock,
    ) -> None:
        """Test fixup PR when no changes needed."""
        mock_run.return_value = "[]"
        mock_existing.return_value = None
        mock_sync.return_value = True
        # Same SHA for base and HEAD
        mock_git.side_effect = [
            "",  # checkout -B
            "abc1234567890",  # rev-parse base_branch
            "abc1234567890",  # rev-parse HEAD (same)
        ]

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(
                    config=self.config, dry_run=False
                )

        result = bot.create_or_update_fixup_pr(
            ["fb_custom"], "baseline123", self.upstream_config
        )

        self.assertIsNone(result)


class TestGetCookbooksMissingBaselines(unittest.TestCase):
    """Test get_cookbooks_missing_baselines method."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.config = {
            "bot_label": "line-cook",
            "split_label": "line-cook-pr-split",
            "bot_command_prefix": "#linecook",
            "upstream_overrides": {},
            "universe_upstreams": {},
        }
        self.upstream_config = {
            "prefix": "fb",
            "remote": "fb_upstream",
            "branch": "main",
            "trailer_key": "Upstream-Commit",
            "ignore_cookbooks": [],
        }

    @patch.object(linecook_module.LineCook, "find_baseline_for_cookbook")
    @patch.object(linecook_module.LineCook, "list_local_cookbooks")
    @patch.object(linecook_module, "run")
    def test_get_missing_baselines(
        self,
        mock_run: MagicMock,
        mock_list: MagicMock,
        mock_find: MagicMock,
    ) -> None:
        """Test finding cookbooks without baselines."""
        mock_run.return_value = "[]"
        mock_list.return_value = ["fb_apache", "fb_custom", "fb_mysql"]
        # fb_custom has no baseline
        mock_find.side_effect = [
            "abc1234",
            None,
            "def5678",
        ]

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        result = bot.get_cookbooks_missing_baselines(self.upstream_config)

        self.assertEqual(len(result), 1)
        self.assertIn("fb_custom", result)


if __name__ == "__main__":
    unittest.main()
