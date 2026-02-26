#!/usr/bin/env python3
"""Tests for sync orchestration and pointer management."""

import unittest
from unittest.mock import patch, MagicMock, call
import json
import os
import sys

# Add bin to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))

# Use dynamic import to avoid type checking issues
linecook_module = __import__("line-cook")


class TestGetCurrentPointer(unittest.TestCase):
    """Test get_current_pointer method."""

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

    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_get_pointer_single_trailer(
        self, mock_run: MagicMock, mock_git: MagicMock
    ) -> None:
        """Test getting pointer with single trailer."""
        mock_run.return_value = "[]"
        mock_git.return_value = (
            "Sync fb_apache\n\nUpstream-Commit: abc1234567890"
        )

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        result = bot.get_current_pointer(self.upstream_config)

        self.assertEqual(result, "abc1234567890")

    @patch.object(linecook_module, "try_git")
    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_get_pointer_squash_merge(
        self,
        mock_run: MagicMock,
        mock_git: MagicMock,
        mock_try_git: MagicMock,
    ) -> None:
        """Test getting pointer from squash-merge with multiple trailers."""
        mock_run.return_value = "[]"
        mock_git.return_value = (
            "Squashed commits:\n"
            "* Commit 1\n"
            "  Upstream-Commit: abc1234567890\n"
            "* Commit 2\n"
            "  Upstream-Commit: def4567890123\n"
        )
        # def is ancestor of abc, but abc is not ancestor of def
        # (def is newer)
        mock_try_git.side_effect = [
            (False, "", ""),  # abc not ancestor of def
            (True, "", ""),  # def is ancestor of abc
        ]

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        result = bot.get_current_pointer(self.upstream_config)

        # Should return abc since def is ancestor (abc is newer)
        self.assertEqual(result, "abc1234567890")

    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_get_pointer_no_trailer(
        self, mock_run: MagicMock, mock_git: MagicMock
    ) -> None:
        """Test getting pointer when no trailer exists."""
        mock_run.return_value = "[]"
        mock_git.return_value = "Some commit message\n"

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        result = bot.get_current_pointer(self.upstream_config)

        self.assertIsNone(result)


class TestUpstreamCommitsSince(unittest.TestCase):
    """Test upstream_commits_since method."""

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

    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_upstream_commits_since_with_pointer(
        self, mock_run: MagicMock, mock_git: MagicMock
    ) -> None:
        """Test getting commits since pointer."""
        mock_run.return_value = "[]"
        mock_git.return_value = "commit1\ncommit2\ncommit3"

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        result = bot.upstream_commits_since(
            "abc1234567890", self.upstream_config
        )

        self.assertEqual(len(result), 3)
        self.assertEqual(result, ["commit1", "commit2", "commit3"])

    @patch.object(linecook_module, "run")
    def test_upstream_commits_since_no_pointer(
        self, mock_run: MagicMock
    ) -> None:
        """Test with no pointer (returns empty)."""
        mock_run.return_value = "[]"

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        result = bot.upstream_commits_since(None, self.upstream_config)

        self.assertEqual(len(result), 0)


class TestDetectLocalChanges(unittest.TestCase):
    """Test detect_local_changes method."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.config = {
            "bot_label": "line-cook",
            "split_label": "line-cook-pr-split",
            "bot_command_prefix": "#linecook",
            "upstream_overrides": {},
            "universe_upstreams": {},
        }

    @patch.object(linecook_module, "try_git")
    @patch.object(linecook_module, "run")
    def test_detect_local_changes_present(
        self, mock_run: MagicMock, mock_try_git: MagicMock
    ) -> None:
        """Test detecting local changes when present."""
        mock_run.return_value = "[]"
        mock_try_git.return_value = (False, "", "")  # diff not quiet

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        result = bot.detect_local_changes("fb_apache")

        self.assertTrue(result)

    @patch.object(linecook_module, "try_git")
    @patch.object(linecook_module, "run")
    def test_detect_local_changes_absent(
        self, mock_run: MagicMock, mock_try_git: MagicMock
    ) -> None:
        """Test detecting local changes when absent."""
        mock_run.return_value = "[]"
        mock_try_git.return_value = (True, "", "")  # diff quiet

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        result = bot.detect_local_changes("fb_apache")

        self.assertFalse(result)


class TestCreateOrUpdateIssueForLocalChanges(unittest.TestCase):
    """Test create_or_update_issue_for_local_changes method."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.config = {
            "bot_label": "line-cook",
            "split_label": "line-cook-pr-split",
            "bot_command_prefix": "#linecook",
            "upstream_overrides": {},
            "universe_upstreams": {},
        }

    @patch.object(linecook_module.LineCook, "find_existing_issue_for_cookbook")
    @patch.object(linecook_module, "run")
    def test_create_issue_for_local_changes(
        self,
        mock_run: MagicMock,
        mock_find_issue: MagicMock,
    ) -> None:
        """Test creating issue for local changes."""
        mock_run.side_effect = ["[]", ""]
        mock_find_issue.return_value = None

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(
                    config=self.config, dry_run=False
                )

        bot.create_or_update_issue_for_local_changes(
            ["fb_apache"], "abc1234567890"
        )

        # Should call run once: for issue create (find_existing is mocked)
        self.assertEqual(mock_run.call_count, 1)
        create_call = mock_run.call_args_list[0][0][0]
        self.assertEqual(create_call[0], "gh")
        self.assertEqual(create_call[1], "issue")
        self.assertEqual(create_call[2], "create")

    @patch.object(linecook_module.LineCook, "find_existing_issue_for_cookbook")
    @patch.object(linecook_module, "run")
    def test_update_existing_issue_for_local_changes(
        self,
        mock_run: MagicMock,
        mock_find_issue: MagicMock,
    ) -> None:
        """Test updating existing issue for local changes."""
        mock_run.side_effect = ["[]", ""]
        mock_find_issue.return_value = 42

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(
                    config=self.config, dry_run=False
                )

        bot.create_or_update_issue_for_local_changes(
            ["fb_apache"], "abc1234567890"
        )

        # Should call run once: for issue edit (find_existing is mocked)
        self.assertEqual(mock_run.call_count, 1)
        edit_call = mock_run.call_args_list[0][0][0]
        self.assertEqual(edit_call[0], "gh")
        self.assertEqual(edit_call[1], "issue")
        self.assertEqual(edit_call[2], "edit")


class TestSyncOrchestration(unittest.TestCase):
    """Test sync orchestration methods."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.config = {
            "bot_label": "line-cook",
            "split_label": "line-cook-pr-split",
            "bot_command_prefix": "#linecook",
            "upstream_overrides": {},
            "universe_upstreams": {},
        }

    @patch.object(linecook_module.LineCook, "_sync_upstream")
    @patch.object(linecook_module.LineCook, "fetch_upstream")
    @patch.object(linecook_module, "run")
    def test_sync_all_upstreams(
        self,
        mock_run: MagicMock,
        mock_fetch: MagicMock,
        mock_sync_upstream: MagicMock,
    ) -> None:
        """Test syncing all configured upstreams."""
        mock_run.return_value = "[]"

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        bot.sync()

        # Should fetch all upstreams
        mock_fetch.assert_called_once()
        # Should sync primary upstream (fb)
        mock_sync_upstream.assert_called_once()

    @patch.object(linecook_module.LineCook, "create_onboarding_pr")
    @patch.object(linecook_module.LineCook, "detect_global_baseline")
    @patch.object(linecook_module.LineCook, "get_current_pointer")
    @patch.object(linecook_module.LineCook, "fetch_upstream")
    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_sync_onboarding_mode(
        self,
        mock_run: MagicMock,
        mock_git: MagicMock,
        mock_fetch: MagicMock,
        mock_get_pointer: MagicMock,
        mock_detect_baseline: MagicMock,
        mock_create_onboarding: MagicMock,
    ) -> None:
        """Test sync in onboarding mode (no pointer)."""
        mock_run.return_value = "[]"
        mock_git.return_value = ""
        mock_get_pointer.return_value = None
        mock_detect_baseline.return_value = ("baseline123", [])
        mock_create_onboarding.return_value = 50

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        bot.sync()

        mock_detect_baseline.assert_called_once()
        mock_create_onboarding.assert_called_once_with(
            "baseline123", "Upstream-Commit", "fb"
        )

    @patch.object(linecook_module.LineCook, "create_or_update_fixup_pr")
    @patch.object(linecook_module.LineCook, "detect_global_baseline")
    @patch.object(linecook_module.LineCook, "get_current_pointer")
    @patch.object(linecook_module.LineCook, "fetch_upstream")
    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_sync_onboarding_with_missing_baselines(
        self,
        mock_run: MagicMock,
        mock_git: MagicMock,
        mock_fetch: MagicMock,
        mock_get_pointer: MagicMock,
        mock_detect_baseline: MagicMock,
        mock_create_fixup: MagicMock,
    ) -> None:
        """Test onboarding with cookbooks missing baselines."""
        mock_run.return_value = "[]"
        mock_git.return_value = ""
        mock_get_pointer.return_value = None
        mock_detect_baseline.return_value = (
            "baseline123",
            ["fb_custom"],
        )
        mock_create_fixup.return_value = 51

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        bot.sync()

        mock_detect_baseline.assert_called_once()
        mock_create_fixup.assert_called_once()

    @patch.object(linecook_module.LineCook, "create_pr")
    @patch.object(linecook_module.LineCook, "existing_sync_pr")
    @patch.object(linecook_module.LineCook, "cherry_pick_with_trailer")
    @patch.object(linecook_module.LineCook, "list_local_cookbooks")
    @patch.object(linecook_module.LineCook, "close_resolved_conflict_issues")
    @patch.object(linecook_module.LineCook, "upstream_commits_since")
    @patch.object(linecook_module.LineCook, "get_current_pointer")
    @patch.object(linecook_module.LineCook, "fetch_upstream")
    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_sync_normal_mode_with_commits(
        self,
        mock_run: MagicMock,
        mock_git: MagicMock,
        mock_fetch: MagicMock,
        mock_get_pointer: MagicMock,
        mock_upstream_commits: MagicMock,
        mock_close_issues: MagicMock,
        mock_list_cookbooks: MagicMock,
        mock_cherry_pick: MagicMock,
        mock_existing_pr: MagicMock,
        mock_create_pr: MagicMock,
    ) -> None:
        """Test normal sync mode with commits to apply."""
        mock_run.return_value = "[]"
        mock_git.side_effect = [
            "",  # checkout base_branch
            "",  # checkout -B sync branch
            "cookbooks/fb_apache/file.rb",  # show --name-only
            "",  # push
        ]
        mock_get_pointer.return_value = "pointer123"
        mock_upstream_commits.return_value = ["commit1"]
        mock_list_cookbooks.return_value = ["fb_apache"]
        mock_cherry_pick.return_value = True
        mock_existing_pr.return_value = None
        mock_create_pr.return_value = 100

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(
                    config=self.config, dry_run=False
                )

        bot.sync()

        mock_cherry_pick.assert_called_once()
        mock_create_pr.assert_called_once()
        mock_close_issues.assert_called()

    @patch.object(
        linecook_module.LineCook,
        "create_or_update_issue_for_local_changes",
    )
    @patch.object(linecook_module.LineCook, "detect_local_changes")
    @patch.object(linecook_module.LineCook, "list_local_cookbooks")
    @patch.object(linecook_module.LineCook, "close_resolved_conflict_issues")
    @patch.object(linecook_module.LineCook, "upstream_commits_since")
    @patch.object(linecook_module.LineCook, "get_current_pointer")
    @patch.object(linecook_module.LineCook, "fetch_upstream")
    @patch("subprocess.run")
    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_sync_no_commits_with_local_changes(
        self,
        mock_run: MagicMock,
        mock_git: MagicMock,
        mock_subprocess: MagicMock,
        mock_fetch: MagicMock,
        mock_get_pointer: MagicMock,
        mock_upstream_commits: MagicMock,
        mock_close_issues: MagicMock,
        mock_list_cookbooks: MagicMock,
        mock_detect_changes: MagicMock,
        mock_create_issue: MagicMock,
    ) -> None:
        """Test sync with no commits but local changes detected."""
        mock_run.return_value = "[]"
        mock_git.side_effect = [
            "",  # checkout base_branch
        ]
        mock_get_pointer.return_value = "pointer123"
        mock_upstream_commits.return_value = []
        mock_list_cookbooks.return_value = ["fb_apache", "fb_mysql"]
        mock_detect_changes.side_effect = [True, False]

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(
                    config=self.config, dry_run=False
                )

        bot.sync()

        # Should create issue for fb_apache but not fb_mysql
        mock_create_issue.assert_called_once()
        call_args = mock_create_issue.call_args[0]
        self.assertIn("fb_apache", call_args[0])

    @patch.object(linecook_module.LineCook, "cherry_pick_with_trailer")
    @patch.object(linecook_module.LineCook, "create_conflict_issue")
    @patch.object(linecook_module.LineCook, "list_local_cookbooks")
    @patch.object(linecook_module.LineCook, "upstream_commits_since")
    @patch.object(linecook_module.LineCook, "get_current_pointer")
    @patch.object(linecook_module.LineCook, "fetch_upstream")
    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_sync_with_conflict(
        self,
        mock_run: MagicMock,
        mock_git: MagicMock,
        mock_fetch: MagicMock,
        mock_get_pointer: MagicMock,
        mock_upstream_commits: MagicMock,
        mock_list_cookbooks: MagicMock,
        mock_create_issue: MagicMock,
        mock_cherry_pick: MagicMock,
    ) -> None:
        """Test sync that encounters conflict."""
        mock_run.return_value = "[]"
        mock_git.side_effect = [
            "",  # checkout base_branch
            "",  # checkout -B sync branch
            "cookbooks/fb_apache/file.rb",  # show --name-only
        ]
        mock_get_pointer.return_value = "pointer123"
        mock_upstream_commits.return_value = ["commit1"]
        mock_list_cookbooks.return_value = ["fb_apache"]
        mock_cherry_pick.side_effect = RuntimeError("Conflict")

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        # Store conflict details for the exception
        bot._last_conflict_details = "conflict info"

        bot.sync()

        mock_cherry_pick.assert_called_once()
        mock_create_issue.assert_called_once()


class TestFetchUpstream(unittest.TestCase):
    """Test fetch_upstream method."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.config = {
            "bot_label": "line-cook",
            "split_label": "line-cook-pr-split",
            "bot_command_prefix": "#linecook",
            "upstream_overrides": {},
            "universe_upstreams": {
                "pd": {"prefix": "pd", "repo_url": "test.git"}
            },
        }

    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_fetch_specific_upstream(
        self, mock_run: MagicMock, mock_git: MagicMock
    ) -> None:
        """Test fetching specific upstream."""
        mock_run.return_value = "[]"
        mock_git.return_value = ""

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        upstream = bot.upstreams["fb"]
        bot.fetch_upstream(upstream)

        mock_git.assert_called_once_with("fetch", "fb_upstream")

    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_fetch_all_upstreams(
        self, mock_run: MagicMock, mock_git: MagicMock
    ) -> None:
        """Test fetching all upstreams."""
        mock_run.return_value = "[]"
        mock_git.return_value = ""

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        bot.fetch_upstream(None)

        # Should fetch both fb and pd upstreams
        self.assertEqual(mock_git.call_count, 2)


if __name__ == "__main__":
    unittest.main()
