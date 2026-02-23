#!/usr/bin/env python3
"""Tests for cherry-pick and commit filtering operations."""

import unittest
from unittest.mock import patch, MagicMock, call
import os
import sys

# Add bin to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))

# Use dynamic import to avoid type checking issues
linecook_module = __import__("line-cook")


class TestCherryPickWithTrailer(unittest.TestCase):
    """Test cherry_pick_with_trailer method."""

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

    @patch.object(linecook_module.LineCook, "is_commit_already_applied")
    @patch.object(linecook_module.LineCook, "filter_and_commit_fb_changes")
    @patch.object(linecook_module, "try_git")
    @patch.object(linecook_module, "run")
    def test_cherry_pick_success_with_changes(
        self,
        mock_run: MagicMock,
        mock_try_git: MagicMock,
        mock_filter: MagicMock,
        mock_already_applied: MagicMock,
    ) -> None:
        """Test successful cherry-pick with changes."""
        mock_run.return_value = "[]"
        mock_already_applied.return_value = False
        mock_try_git.return_value = (True, "", "")
        mock_filter.return_value = True

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        result = bot.cherry_pick_with_trailer(
            "abc1234567890", self.upstream_config
        )

        self.assertTrue(result)
        mock_already_applied.assert_called_once()
        mock_try_git.assert_called_once()
        mock_filter.assert_called_once()

    @patch.object(linecook_module.LineCook, "is_commit_already_applied")
    @patch.object(linecook_module, "run")
    def test_cherry_pick_skip_already_applied(
        self,
        mock_run: MagicMock,
        mock_already_applied: MagicMock,
    ) -> None:
        """Test skipping already applied commit."""
        mock_run.return_value = "[]"
        mock_already_applied.return_value = True

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        result = bot.cherry_pick_with_trailer(
            "abc1234567890", self.upstream_config
        )

        self.assertFalse(result)
        mock_already_applied.assert_called_once()

    @patch.object(linecook_module.LineCook, "is_commit_already_applied")
    @patch.object(linecook_module.LineCook, "_abort_cherry_pick_safely")
    @patch.object(linecook_module.LineCook, "_categorize_conflicts")
    @patch.object(linecook_module.LineCook, "_get_conflicting_files")
    @patch.object(linecook_module.LineCook, "_capture_basic_conflict_info")
    @patch.object(linecook_module, "try_git")
    @patch.object(linecook_module, "run")
    def test_cherry_pick_conflict_resolution(
        self,
        mock_run: MagicMock,
        mock_try_git: MagicMock,
        mock_basic_info: MagicMock,
        mock_get_conflicts: MagicMock,
        mock_categorize: MagicMock,
        mock_abort: MagicMock,
        mock_already_applied: MagicMock,
    ) -> None:
        """Test cherry-pick with auto-resolvable conflicts."""
        mock_run.return_value = "[]"
        mock_already_applied.return_value = False
        mock_try_git.return_value = (False, "", "conflict error")
        mock_get_conflicts.return_value = ["cookbooks/pd_other/file.rb"]
        mock_categorize.return_value = ([], ["cookbooks/pd_other/file.rb"])
        mock_basic_info.return_value = "basic conflict info"

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        result = bot.cherry_pick_with_trailer(
            "abc1234567890", self.upstream_config
        )

        self.assertFalse(result)
        mock_abort.assert_called_once()


class TestFilterAndCommit(unittest.TestCase):
    """Test filter_and_commit_fb_changes method."""

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

    @patch.object(linecook_module.LineCook, "list_local_cookbooks")
    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_filter_with_matching_files(
        self,
        mock_run: MagicMock,
        mock_git: MagicMock,
        mock_list_cookbooks: MagicMock,
    ) -> None:
        """Test filtering with matching fb_ cookbook files."""
        mock_run.return_value = "[]"
        mock_list_cookbooks.return_value = ["fb_apache", "fb_mysql"]

        # Mock git status output
        mock_git.side_effect = [
            None,  # reset HEAD
            "M  cookbooks/fb_apache/file.rb\nM  cookbooks/other/file.rb",
            None,  # add
            "commit message",  # show -s --format=%B
            None,  # commit
        ]

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        result = bot.filter_and_commit_fb_changes(
            "abc1234567890", self.upstream_config
        )

        self.assertTrue(result)
        # Verify git add was called with fb_apache file
        calls = mock_git.call_args_list
        self.assertTrue(
            any("cookbooks/fb_apache/file.rb" in str(c) for c in calls)
        )

    @patch.object(linecook_module.LineCook, "list_local_cookbooks")
    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_filter_with_no_matching_files(
        self,
        mock_run: MagicMock,
        mock_git: MagicMock,
        mock_list_cookbooks: MagicMock,
    ) -> None:
        """Test filtering when no fb_ cookbook files match."""
        mock_run.return_value = "[]"
        mock_list_cookbooks.return_value = ["fb_apache"]

        # Mock git status output - only non-fb files
        mock_git.side_effect = [
            None,  # reset HEAD
            "M  cookbooks/other/file.rb",
            None,  # cherry-pick --abort or reset
        ]

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        result = bot.filter_and_commit_fb_changes(
            "abc1234567890", self.upstream_config
        )

        self.assertFalse(result)


class TestIsCommitAlreadyApplied(unittest.TestCase):
    """Test is_commit_already_applied method."""

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

    @patch.object(linecook_module.LineCook, "list_local_cookbooks")
    @patch.object(linecook_module, "try_git")
    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_commit_already_applied(
        self,
        mock_run: MagicMock,
        mock_git: MagicMock,
        mock_try_git: MagicMock,
        mock_list_cookbooks: MagicMock,
    ) -> None:
        """Test when commit is already fully applied."""
        mock_run.return_value = "[]"
        mock_list_cookbooks.return_value = ["fb_apache"]
        mock_git.return_value = "cookbooks/fb_apache/file.rb"
        # Same content at commit and HEAD
        mock_try_git.side_effect = [
            (True, "file content", ""),
            (True, "file content", ""),
        ]

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        result = bot.is_commit_already_applied(
            "abc1234567890", self.upstream_config
        )

        self.assertTrue(result)

    @patch.object(linecook_module.LineCook, "list_local_cookbooks")
    @patch.object(linecook_module, "try_git")
    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_commit_not_applied(
        self,
        mock_run: MagicMock,
        mock_git: MagicMock,
        mock_try_git: MagicMock,
        mock_list_cookbooks: MagicMock,
    ) -> None:
        """Test when commit is not yet applied."""
        mock_run.return_value = "[]"
        mock_list_cookbooks.return_value = ["fb_apache"]
        mock_git.return_value = "cookbooks/fb_apache/file.rb"
        # Different content at commit and HEAD
        mock_try_git.side_effect = [
            (True, "new content", ""),
            (True, "old content", ""),
        ]

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        result = bot.is_commit_already_applied(
            "abc1234567890", self.upstream_config
        )

        self.assertFalse(result)

    @patch.object(linecook_module.LineCook, "list_local_cookbooks")
    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_commit_with_no_relevant_files(
        self,
        mock_run: MagicMock,
        mock_git: MagicMock,
        mock_list_cookbooks: MagicMock,
    ) -> None:
        """Test when commit has no relevant fb_ files."""
        mock_run.return_value = "[]"
        mock_list_cookbooks.return_value = ["fb_apache"]
        # Commit only touches non-fb files
        mock_git.return_value = "cookbooks/other/file.rb"

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        result = bot.is_commit_already_applied(
            "abc1234567890", self.upstream_config
        )

        # No relevant changes = considered "applied"
        self.assertTrue(result)


class TestListLocalCookbooks(unittest.TestCase):
    """Test list_local_cookbooks method."""

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
            "ignore_cookbooks": ["fb_init"],
        }

    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_list_local_cookbooks_fb(
        self, mock_run: MagicMock, mock_git: MagicMock
    ) -> None:
        """Test listing fb_ cookbooks."""
        mock_run.return_value = "[]"
        mock_git.return_value = (
            "cookbooks/fb_apache\n"
            "cookbooks/fb_mysql\n"
            "cookbooks/fb_init\n"
            "cookbooks/other\n"
        )

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        result = bot.list_local_cookbooks(self.upstream_config)

        # Should include fb_apache and fb_mysql, but not fb_init (ignored)
        # or other
        self.assertEqual(len(result), 2)
        self.assertIn("fb_apache", result)
        self.assertIn("fb_mysql", result)
        self.assertNotIn("fb_init", result)
        self.assertNotIn("other", result)

    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_list_local_cookbooks_multiple_upstreams(
        self, mock_run: MagicMock, mock_git: MagicMock
    ) -> None:
        """Test filtering cookbooks by upstream prefix."""
        config = self.config.copy()
        config["universe_upstreams"] = {
            "pd": {"prefix": "pd", "repo_url": "test.git"}
        }
        mock_run.return_value = "[]"
        mock_git.return_value = (
            "cookbooks/fb_apache\n"
            "cookbooks/pd_other\n"
            "cookbooks/xyz_test\n"
        )

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=config, dry_run=True)

        # Test fb upstream
        fb_upstream = {
            "prefix": "fb",
            "remote": "fb_upstream",
            "trailer_key": "Upstream-Commit",
            "ignore_cookbooks": [],
        }
        result = bot.list_local_cookbooks(fb_upstream)
        self.assertEqual(result, ["fb_apache"])

        # Test pd upstream
        pd_upstream = {
            "prefix": "pd",
            "remote": "pd_upstream",
            "trailer_key": "pd_Upstream-Commit",
            "ignore_cookbooks": [],
        }
        result = bot.list_local_cookbooks(pd_upstream)
        self.assertEqual(result, ["pd_other"])


if __name__ == "__main__":
    unittest.main()
