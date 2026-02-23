#!/usr/bin/env python3
"""Tests for conflict detection and handling."""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import os
import sys

# Add bin to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))

# Use dynamic import to avoid type checking issues
linecook_module = __import__("line-cook")


class TestGetConflictingFiles(unittest.TestCase):
    """Test _get_conflicting_files method."""

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
    def test_get_conflicting_files(
        self, mock_run: MagicMock, mock_git: MagicMock
    ) -> None:
        """Test extracting conflicting files from git status."""
        mock_run.return_value = "[]"
        mock_git.return_value = (
            "UU cookbooks/fb_apache/metadata.rb\n"
            "AA cookbooks/fb_mysql/recipes/default.rb\n"
            "M  cookbooks/fb_other/file.rb\n"
        )

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        result = bot._get_conflicting_files()

        self.assertEqual(len(result), 2)
        self.assertIn("cookbooks/fb_apache/metadata.rb", result)
        self.assertIn("cookbooks/fb_mysql/recipes/default.rb", result)
        self.assertNotIn("cookbooks/fb_other/file.rb", result)

    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_get_conflicting_files_empty(
        self, mock_run: MagicMock, mock_git: MagicMock
    ) -> None:
        """Test when no conflicts exist."""
        mock_run.return_value = "[]"
        mock_git.return_value = "M  cookbooks/fb_apache/file.rb\n"

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        result = bot._get_conflicting_files()

        self.assertEqual(len(result), 0)


class TestCategorizeConflicts(unittest.TestCase):
    """Test _categorize_conflicts method."""

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
    @patch.object(linecook_module, "run")
    def test_categorize_real_conflicts(
        self, mock_run: MagicMock, mock_list_cookbooks: MagicMock
    ) -> None:
        """Test categorizing conflicts in local cookbooks."""
        mock_run.return_value = "[]"
        mock_list_cookbooks.return_value = ["fb_apache", "fb_mysql"]

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        files = [
            "cookbooks/fb_apache/metadata.rb",
            "cookbooks/fb_other/file.rb",
            "cookbooks/pd_test/file.rb",
        ]

        real, auto_resolve = bot._categorize_conflicts(
            files, self.upstream_config
        )

        self.assertEqual(len(real), 1)
        self.assertIn("cookbooks/fb_apache/metadata.rb", real)
        self.assertEqual(len(auto_resolve), 2)

    @patch.object(linecook_module.LineCook, "list_local_cookbooks")
    @patch.object(linecook_module, "run")
    def test_categorize_only_auto_resolve(
        self, mock_run: MagicMock, mock_list_cookbooks: MagicMock
    ) -> None:
        """Test categorizing with only auto-resolvable conflicts."""
        mock_run.return_value = "[]"
        mock_list_cookbooks.return_value = ["fb_apache"]

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        files = [
            "cookbooks/fb_other/file.rb",
            "cookbooks/pd_test/file.rb",
        ]

        real, auto_resolve = bot._categorize_conflicts(
            files, self.upstream_config
        )

        self.assertEqual(len(real), 0)
        self.assertEqual(len(auto_resolve), 2)


class TestCaptureConflictDetails(unittest.TestCase):
    """Test capture_conflict_details method."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.config = {
            "bot_label": "line-cook",
            "split_label": "line-cook-pr-split",
            "bot_command_prefix": "#linecook",
            "upstream_overrides": {},
            "universe_upstreams": {},
        }

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="<<<<<<< HEAD\nlocal\n=======\nupstream\n>>>>>>> abc1234",
    )
    @patch.object(linecook_module, "run")
    def test_capture_conflict_details(
        self, mock_run: MagicMock, mock_file: MagicMock
    ) -> None:
        """Test capturing conflict details from files."""
        mock_run.return_value = "[]"

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        files = ["cookbooks/fb_apache/metadata.rb"]
        result = bot.capture_conflict_details(files)

        self.assertIn("### cookbooks/fb_apache/metadata.rb", result)
        self.assertIn("<<<<<<< HEAD", result)

    @patch("builtins.open", side_effect=FileNotFoundError())
    @patch.object(linecook_module, "run")
    def test_capture_conflict_details_file_not_found(
        self, mock_run: MagicMock, mock_file: MagicMock
    ) -> None:
        """Test capturing conflict details when file doesn't exist."""
        mock_run.return_value = "[]"

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        files = ["cookbooks/fb_apache/metadata.rb"]
        result = bot.capture_conflict_details(files)

        self.assertIn("Could not read file", result)


class TestCreateConflictIssue(unittest.TestCase):
    """Test create_conflict_issue method."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.config = {
            "bot_label": "line-cook",
            "split_label": "line-cook-pr-split",
            "bot_command_prefix": "#linecook",
            "upstream_overrides": {},
            "universe_upstreams": {},
        }

    @patch.object(linecook_module.LineCook, "close_resolved_conflict_issues")
    @patch("subprocess.run")
    @patch.object(linecook_module, "run")
    def test_create_new_conflict_issue(
        self,
        mock_run: MagicMock,
        mock_subprocess: MagicMock,
        mock_close_resolved: MagicMock,
    ) -> None:
        """Test creating new conflict issue."""
        # First call returns empty list (no existing issues)
        # Second call is the actual create
        mock_run.side_effect = ["[]", ""]

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(
                    config=self.config, dry_run=False
                )

        bot.create_conflict_issue(
            "abc1234567890",
            cookbooks=["fb_apache"],
            conflict_details="conflict info",
        )

        # Three calls: list existing, close_resolved list (mocked), create
        self.assertEqual(mock_run.call_count, 2)
        # Check that gh issue create was called
        create_call = mock_run.call_args_list[1][0][0]
        self.assertEqual(create_call[0], "gh")
        self.assertEqual(create_call[1], "issue")
        self.assertEqual(create_call[2], "create")

    @patch.object(linecook_module.LineCook, "close_resolved_conflict_issues")
    @patch("subprocess.run")
    @patch.object(linecook_module, "run")
    def test_update_existing_conflict_issue(
        self,
        mock_run: MagicMock,
        mock_subprocess: MagicMock,
        mock_close_resolved: MagicMock,
    ) -> None:
        """Test updating existing conflict issue."""
        # First call returns existing issue
        existing_issue = [
            {
                "number": 42,
                "title": "Sync conflict applying upstream commit abc12345",
            }
        ]
        mock_run.side_effect = [
            json.dumps(existing_issue),
            "",
        ]

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(
                    config=self.config, dry_run=False
                )

        bot.create_conflict_issue(
            "abc1234567890",
            cookbooks=["fb_apache"],
        )

        # Two calls: list existing issues, edit
        self.assertEqual(mock_run.call_count, 2)
        # Check that gh issue edit was called
        edit_call = mock_run.call_args_list[1][0][0]
        self.assertEqual(edit_call[0], "gh")
        self.assertEqual(edit_call[1], "issue")
        self.assertEqual(edit_call[2], "edit")


class TestCloseResolvedConflictIssues(unittest.TestCase):
    """Test close_resolved_conflict_issues method."""

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
    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_close_resolved_issues(
        self,
        mock_run: MagicMock,
        mock_git: MagicMock,
        mock_try_git: MagicMock,
    ) -> None:
        """Test closing issues for resolved commits."""
        # Setup: open conflict issue for an old commit
        issues = [
            {
                "number": 10,
                "title": "Sync conflict applying upstream commit abc12345",
            }
        ]
        mock_run.side_effect = [
            json.dumps(issues),
            "",  # comment
            "",  # close
        ]
        mock_git.return_value = "abc1234567890abcdef1234567890abcdef123456"
        # Commit is an ancestor but not the same
        mock_try_git.return_value = (True, "", "")

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(
                    config=self.config, dry_run=False
                )

        bot.close_resolved_conflict_issues("def4567890abcdef")

        # Should call run 3 times: list issues, comment, close
        self.assertEqual(mock_run.call_count, 3)

    @patch.object(linecook_module, "try_git")
    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_keep_current_blocker_open(
        self,
        mock_run: MagicMock,
        mock_git: MagicMock,
        mock_try_git: MagicMock,
    ) -> None:
        """Test that current blocker issue stays open."""
        # Setup: conflict issue for the current commit
        current_commit = "abc1234567890abcdef1234567890abcdef123456"
        issues = [
            {
                "number": 10,
                "title": "Sync conflict applying upstream commit abc12345",
            }
        ]
        mock_run.side_effect = [json.dumps(issues)]
        mock_git.return_value = current_commit
        # Same commit - not an ancestor
        mock_try_git.return_value = (True, "", "")

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(
                    config=self.config, dry_run=False
                )

        bot.close_resolved_conflict_issues(current_commit)

        # Should only call list once, not close
        self.assertEqual(mock_run.call_count, 1)


class TestCaptureBasicConflictInfo(unittest.TestCase):
    """Test _capture_basic_conflict_info method."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.config = {
            "bot_label": "line-cook",
            "split_label": "line-cook-pr-split",
            "bot_command_prefix": "#linecook",
            "upstream_overrides": {},
            "universe_upstreams": {},
        }

    @patch.object(linecook_module.LineCook, "capture_conflict_details")
    @patch.object(linecook_module.LineCook, "_get_conflicting_files")
    @patch.object(linecook_module, "run")
    def test_capture_basic_conflict_info_success(
        self,
        mock_run: MagicMock,
        mock_get_files: MagicMock,
        mock_capture: MagicMock,
    ) -> None:
        """Test capturing basic conflict info successfully."""
        mock_run.return_value = "[]"
        mock_get_files.return_value = ["cookbooks/fb_apache/file.rb"]
        mock_capture.return_value = "conflict details"

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        result = bot._capture_basic_conflict_info()

        self.assertEqual(result, "conflict details")

    @patch.object(linecook_module.LineCook, "_get_conflicting_files")
    @patch.object(linecook_module, "run")
    def test_capture_basic_conflict_info_error(
        self,
        mock_run: MagicMock,
        mock_get_files: MagicMock,
    ) -> None:
        """Test capturing basic conflict info with error."""
        mock_run.return_value = "[]"
        mock_get_files.side_effect = RuntimeError("git error")

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        result = bot._capture_basic_conflict_info()

        self.assertIn("Could not capture", result)


class TestAbortCherryPickSafely(unittest.TestCase):
    """Test _abort_cherry_pick_safely method."""

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
    def test_abort_cherry_pick_success(
        self, mock_run: MagicMock, mock_git: MagicMock
    ) -> None:
        """Test successful cherry-pick abort."""
        mock_run.return_value = "[]"
        mock_git.return_value = ""

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        bot._abort_cherry_pick_safely()

        # Should call cherry-pick --abort
        mock_git.assert_called_once_with("cherry-pick", "--abort")

    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_abort_cherry_pick_fallback(
        self, mock_run: MagicMock, mock_git: MagicMock
    ) -> None:
        """Test cherry-pick abort with fallback to reset."""
        mock_run.return_value = "[]"
        # First call (abort) fails, then reset and clean succeed
        mock_git.side_effect = [
            RuntimeError("no cherry-pick in progress"),
            "",  # reset --hard
            "",  # clean -fd
        ]

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        bot._abort_cherry_pick_safely()

        # Should call abort, then reset and clean
        self.assertEqual(mock_git.call_count, 3)


if __name__ == "__main__":
    unittest.main()
