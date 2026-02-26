#!/usr/bin/env python3
"""Tests for command parsing and handling."""

import unittest
from unittest.mock import patch, MagicMock, call
import json
import os
import sys

# Add bin to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))

# Use dynamic import to avoid type checking issues
linecook_module = __import__("line-cook")


class TestCommandParsing(unittest.TestCase):
    """Test command parsing methods."""

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
    def test_parse_command_split(
        self, mock_run: MagicMock, mock_subprocess: MagicMock
    ) -> None:
        """Test parsing split command."""
        mock_run.return_value = "[]"
        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        result = bot.parse_command("#linecook split abc123-def456")
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "split")
        self.assertEqual(result[1], "abc123-def456")

    @patch("subprocess.run")
    @patch.object(linecook_module, "run")
    def test_parse_command_rebase(
        self, mock_run: MagicMock, mock_subprocess: MagicMock
    ) -> None:
        """Test parsing rebase command."""
        mock_run.return_value = "[]"
        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        result = bot.parse_command("#linecook rebase")
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "rebase")
        self.assertEqual(result[1], "")

    @patch("subprocess.run")
    @patch.object(linecook_module, "run")
    def test_parse_command_invalid(
        self, mock_run: MagicMock, mock_subprocess: MagicMock
    ) -> None:
        """Test parsing invalid command."""
        mock_run.return_value = "[]"
        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        result = bot.parse_command("random comment")
        self.assertIsNone(result)

    @patch("subprocess.run")
    @patch.object(linecook_module, "run")
    def test_parse_split_args_valid(
        self, mock_run: MagicMock, mock_subprocess: MagicMock
    ) -> None:
        """Test parsing valid split arguments."""
        mock_run.return_value = "[]"
        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        result = bot.parse_split_args("abc1234-def5678")
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "abc1234")
        self.assertEqual(result[1], "def5678")

    @patch("subprocess.run")
    @patch.object(linecook_module, "run")
    def test_parse_split_args_invalid(
        self, mock_run: MagicMock, mock_subprocess: MagicMock
    ) -> None:
        """Test parsing invalid split arguments."""
        mock_run.return_value = "[]"
        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        result = bot.parse_split_args("invalid")
        self.assertIsNone(result)

        result = bot.parse_split_args("too-many-parts-here")
        self.assertIsNone(result)


class TestPRFromCommands(unittest.TestCase):
    """Test determining upstream from PR context."""

    @patch("subprocess.run")
    @patch.object(linecook_module, "run")
    def test_determine_upstream_from_branch_name(
        self, mock_run: MagicMock, mock_subprocess: MagicMock
    ) -> None:
        """Test upstream detection from branch name."""
        config = {
            "bot_label": "line-cook",
            "split_label": "line-cook-pr-split",
            "bot_command_prefix": "#linecook",
            "upstream_overrides": {},
            "universe_upstreams": {
                "pd": {"prefix": "pd", "repo_url": "test.git"}
            },
        }
        mock_run.return_value = "[]"

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=config, dry_run=True)

        pr = {"headRefName": "line-cook/pd_update", "body": ""}
        upstream = bot._determine_upstream_from_pr(pr)
        self.assertIsNotNone(upstream)
        self.assertEqual(upstream["prefix"], "pd")

    @patch("subprocess.run")
    @patch.object(linecook_module, "run")
    def test_determine_upstream_from_trailer_primary(
        self, mock_run: MagicMock, mock_subprocess: MagicMock
    ) -> None:
        """Test upstream detection from primary trailer in PR body."""
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

        pr = {
            "headRefName": "some-branch",
            "body": "Some changes\nUpstream-Commit: abc1234567",
        }
        upstream = bot._determine_upstream_from_pr(pr)
        self.assertIsNotNone(upstream)
        self.assertEqual(upstream["prefix"], "fb")

    @patch("subprocess.run")
    @patch.object(linecook_module, "run")
    def test_determine_upstream_from_trailer_non_primary(
        self, mock_run: MagicMock, mock_subprocess: MagicMock
    ) -> None:
        """Test upstream detection from non-primary trailer."""
        config = {
            "bot_label": "line-cook",
            "split_label": "line-cook-pr-split",
            "bot_command_prefix": "#linecook",
            "upstream_overrides": {},
            "universe_upstreams": {
                "pd": {"prefix": "pd", "repo_url": "test.git"}
            },
        }
        mock_run.return_value = "[]"

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=config, dry_run=True)

        pr = {
            "headRefName": "some-branch",
            "body": "Some changes\npd_Upstream-Commit: abc1234567",
        }
        upstream = bot._determine_upstream_from_pr(pr)
        self.assertIsNotNone(upstream)
        self.assertEqual(upstream["prefix"], "pd")


class TestCmdSplit(unittest.TestCase):
    """Test cmd_split command handler."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.config = {
            "bot_label": "line-cook",
            "split_label": "line-cook-pr-split",
            "bot_command_prefix": "#linecook",
            "upstream_overrides": {},
            "universe_upstreams": {},
        }

    @patch.object(linecook_module.LineCook, "add_comment")
    @patch.object(linecook_module.LineCook, "create_pr")
    @patch.object(linecook_module.LineCook, "update_pr_body")
    @patch.object(linecook_module.LineCook, "cherry_pick_with_trailer")
    @patch.object(linecook_module.LineCook, "get_branch_commits_with_trailers")
    @patch.object(linecook_module.LineCook, "_determine_upstream_from_pr")
    @patch("subprocess.run")
    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_cmd_split_basic(
        self,
        mock_run: MagicMock,
        mock_git: MagicMock,
        mock_subprocess: MagicMock,
        mock_determine_upstream: MagicMock,
        mock_get_trailers: MagicMock,
        mock_cherry_pick: MagicMock,
        mock_update_body: MagicMock,
        mock_create_pr: MagicMock,
        mock_add_comment: MagicMock,
    ) -> None:
        """Test basic split operation."""
        # Setup PR data
        pr_data = {
            "number": 123,
            "headRefName": "line-cook/fb_/update",
            "body": (
                "Upstream commits:\n"
                "Upstream-Commit: aaaa1234567890123456789012345678901234ab\n"
                "Upstream-Commit: bbbb1234567890123456789012345678901234ab\n"
                "Upstream-Commit: cccc1234567890123456789012345678901234ab\n"
            ),
        }

        upstream_config = {
            "prefix": "fb",
            "remote": "fb_upstream",
            "trailer_key": "Upstream-Commit",
            "ignore_cookbooks": [],
        }

        mock_run.side_effect = [
            json.dumps(pr_data),  # pr view
            "",  # gh pr edit (add label to first PR)
            "",  # gh pr edit (add label to second PR)
        ]
        mock_determine_upstream.return_value = upstream_config
        mock_get_trailers.return_value = [
            (
                "branch1",
                "aaaa1234567890123456789012345678901234ab",
            ),
            (
                "branch2",
                "bbbb1234567890123456789012345678901234ab",
            ),
            (
                "branch3",
                "cccc1234567890123456789012345678901234ab",
            ),
        ]
        mock_create_pr.return_value = 124

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(
                    config=self.config, dry_run=False
                )

        bot.cmd_split("aaaa1234-bbbb1234", 123)

        # Verify operations
        mock_update_body.assert_called_once()
        mock_create_pr.assert_called_once()
        mock_add_comment.assert_called_once()

    @patch.object(linecook_module, "run")
    def test_cmd_split_invalid_args(self, mock_run: MagicMock) -> None:
        """Test split with invalid arguments."""
        mock_run.return_value = "[]"

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        with self.assertRaises(ValueError):
            bot.cmd_split("invalid", 123)

    @patch.object(linecook_module.LineCook, "_determine_upstream_from_pr")
    @patch("subprocess.run")
    @patch.object(linecook_module, "run")
    def test_cmd_split_no_upstream(
        self,
        mock_run: MagicMock,
        mock_subprocess: MagicMock,
        mock_determine_upstream: MagicMock,
    ) -> None:
        """Test split when upstream cannot be determined."""
        pr_data = {
            "number": 123,
            "headRefName": "some-branch",
            "body": "",
        }
        mock_run.return_value = json.dumps(pr_data)
        mock_determine_upstream.return_value = None

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        with self.assertRaises(ValueError) as ctx:
            bot.cmd_split("aaaa1234-bbbb1234", 123)

        self.assertIn("Could not determine", str(ctx.exception))

    @patch.object(linecook_module.LineCook, "_determine_upstream_from_pr")
    @patch("subprocess.run")
    @patch.object(linecook_module, "run")
    def test_cmd_split_sha_not_in_pr(
        self,
        mock_run: MagicMock,
        mock_subprocess: MagicMock,
        mock_determine_upstream: MagicMock,
    ) -> None:
        """Test split with SHAs not in PR."""
        pr_data = {
            "number": 123,
            "headRefName": "line-cook/fb_/update",
            "body": "Upstream-Commit: aaaa1234567890123456789012345678901234ab\n",
        }

        upstream_config = {
            "prefix": "fb",
            "remote": "fb_upstream",
            "trailer_key": "Upstream-Commit",
            "ignore_cookbooks": [],
        }

        mock_run.return_value = json.dumps(pr_data)
        mock_determine_upstream.return_value = upstream_config

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        with self.assertRaises(ValueError) as ctx:
            bot.cmd_split("bbbb1234-cccc1234", 123)

        self.assertIn("Invalid commit SHAs", str(ctx.exception))

    @patch.object(linecook_module.LineCook, "get_branch_commits_with_trailers")
    @patch.object(linecook_module.LineCook, "_determine_upstream_from_pr")
    @patch("subprocess.run")
    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_cmd_split_middle_range_error(
        self,
        mock_run: MagicMock,
        mock_git: MagicMock,
        mock_subprocess: MagicMock,
        mock_determine_upstream: MagicMock,
        mock_get_commits: MagicMock,
    ) -> None:
        """Test split with middle range (should fail)."""
        pr_data = {
            "number": 123,
            "headRefName": "line-cook/fb_/update",
            "body": (
                "Upstream-Commit: aaaa1234567890123456789012345678901234ab\n"
                "Upstream-Commit: bbbb1234567890123456789012345678901234ab\n"
                "Upstream-Commit: cccc1234567890123456789012345678901234ab\n"
                "Upstream-Commit: dddd1234567890123456789012345678901234ab\n"
            ),
        }

        upstream_config = {
            "prefix": "fb",
            "remote": "fb_upstream",
            "trailer_key": "Upstream-Commit",
            "ignore_cookbooks": [],
        }

        mock_run.return_value = json.dumps(pr_data)
        mock_determine_upstream.return_value = upstream_config
        mock_get_commits.return_value = []

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        # Try to split from middle (not from an end)
        with self.assertRaises(ValueError) as ctx:
            bot.cmd_split("bbbb1234-cccc1234", 123)

        self.assertIn("must be contiguous from one end", str(ctx.exception))


class TestCmdRebase(unittest.TestCase):
    """Test cmd_rebase command handler."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.config = {
            "bot_label": "line-cook",
            "split_label": "line-cook-pr-split",
            "bot_command_prefix": "#linecook",
            "upstream_overrides": {},
            "universe_upstreams": {},
        }

    @patch.object(linecook_module.LineCook, "update_pr_body")
    @patch.object(linecook_module.LineCook, "add_comment")
    @patch.object(linecook_module.LineCook, "_determine_upstream_from_pr")
    @patch("subprocess.run")
    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_cmd_rebase_success(
        self,
        mock_run: MagicMock,
        mock_git: MagicMock,
        mock_subprocess: MagicMock,
        mock_determine_upstream: MagicMock,
        mock_add_comment: MagicMock,
        mock_update_body: MagicMock,
    ) -> None:
        """Test successful rebase."""
        pr_data = {
            "number": 123,
            "headRefName": "line-cook/fb_/update",
            "body": (
                "Upstream-Commit: aaaa1234567890123456789012345678901234ab"
            ),
        }

        upstream_config = {
            "prefix": "fb",
            "remote": "fb_upstream",
            "trailer_key": "Upstream-Commit",
            "ignore_cookbooks": [],
        }

        mock_run.return_value = json.dumps(pr_data)
        mock_determine_upstream.return_value = upstream_config
        mock_git.return_value = ""

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(
                    config=self.config, dry_run=False
                )

        bot.cmd_rebase("", 123)

        # Verify git operations
        git_calls = [str(c) for c in mock_git.call_args_list]
        self.assertTrue(any("fetch" in c for c in git_calls))
        self.assertTrue(any("checkout" in c for c in git_calls))
        self.assertTrue(any("rebase" in c for c in git_calls))
        self.assertTrue(any("push" in c for c in git_calls))
        mock_add_comment.assert_called_once()

    @patch.object(linecook_module.LineCook, "_determine_upstream_from_pr")
    @patch("subprocess.run")
    @patch.object(linecook_module, "git")
    @patch.object(linecook_module, "run")
    def test_cmd_rebase_conflict(
        self,
        mock_run: MagicMock,
        mock_git: MagicMock,
        mock_subprocess: MagicMock,
        mock_determine_upstream: MagicMock,
    ) -> None:
        """Test rebase with conflicts."""
        pr_data = {
            "number": 123,
            "headRefName": "line-cook/fb_/update",
            "body": "Upstream-Commit: aaaa1234567890123456789012345678901234ab",
        }

        upstream_config = {
            "prefix": "fb",
            "remote": "fb_upstream",
            "trailer_key": "Upstream-Commit",
            "ignore_cookbooks": [],
        }

        mock_run.return_value = json.dumps(pr_data)
        mock_determine_upstream.return_value = upstream_config

        # Mock git to succeed for fetch and checkout, fail for rebase
        def git_side_effect(*args):
            if args[0] == "rebase":
                raise RuntimeError("rebase conflict")
            return ""

        mock_git.side_effect = git_side_effect

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(
                    config=self.config, dry_run=False
                )

        with self.assertRaises(ValueError) as ctx:
            bot.cmd_rebase("", 123)

        self.assertIn("Rebase failed with conflicts", str(ctx.exception))

    @patch.object(linecook_module.LineCook, "_determine_upstream_from_pr")
    @patch.object(linecook_module, "run")
    def test_cmd_rebase_no_upstream(
        self,
        mock_run: MagicMock,
        mock_determine_upstream: MagicMock,
    ) -> None:
        """Test rebase when upstream cannot be determined."""
        pr_data = {
            "number": 123,
            "headRefName": "some-branch",
            "body": "",
        }

        mock_run.side_effect = ["[]", json.dumps(pr_data)]
        mock_determine_upstream.return_value = None

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        with self.assertRaises(ValueError) as ctx:
            bot.cmd_rebase("", 123)

        self.assertIn("Could not determine", str(ctx.exception))


class TestHandleCommand(unittest.TestCase):
    """Test handle_command method."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.config = {
            "bot_label": "line-cook",
            "split_label": "line-cook-pr-split",
            "bot_command_prefix": "#linecook",
            "upstream_overrides": {},
            "universe_upstreams": {},
        }

    @patch.object(linecook_module.LineCook, "cmd_split")
    @patch.object(linecook_module.LineCook, "parse_command")
    @patch.object(linecook_module, "run")
    def test_handle_command_split(
        self,
        mock_run: MagicMock,
        mock_parse: MagicMock,
        mock_cmd_split: MagicMock,
    ) -> None:
        """Test handling split command."""
        mock_run.return_value = "[]"
        mock_parse.return_value = ("split", "abc1234-def5678")

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        bot.handle_command("#linecook split abc1234-def5678", 123)

        mock_cmd_split.assert_called_once_with(
            args="abc1234-def5678", pr_number=123
        )

    @patch.object(linecook_module.LineCook, "cmd_rebase")
    @patch.object(linecook_module.LineCook, "parse_command")
    @patch.object(linecook_module, "run")
    def test_handle_command_rebase(
        self,
        mock_run: MagicMock,
        mock_parse: MagicMock,
        mock_cmd_rebase: MagicMock,
    ) -> None:
        """Test handling rebase command."""
        mock_run.return_value = "[]"
        mock_parse.return_value = ("rebase", "")

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        bot.handle_command("#linecook rebase", 123)

        mock_cmd_rebase.assert_called_once_with("", 123)

    @patch.object(linecook_module.LineCook, "add_comment")
    @patch.object(linecook_module.LineCook, "parse_command")
    @patch.object(linecook_module, "run")
    def test_handle_command_unknown(
        self,
        mock_run: MagicMock,
        mock_parse: MagicMock,
        mock_add_comment: MagicMock,
    ) -> None:
        """Test handling unknown command."""
        mock_run.return_value = "[]"
        mock_parse.return_value = ("unknown", "")

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        bot.handle_command("#linecook unknown", 123)

        # Should add error comment
        mock_add_comment.assert_called_once()
        comment_text = mock_add_comment.call_args[0][1]
        self.assertIn("Unknown command", comment_text)

    @patch.object(linecook_module.LineCook, "add_comment")
    @patch.object(linecook_module.LineCook, "cmd_split")
    @patch.object(linecook_module.LineCook, "parse_command")
    @patch.object(linecook_module, "run")
    def test_handle_command_exception(
        self,
        mock_run: MagicMock,
        mock_parse: MagicMock,
        mock_cmd_split: MagicMock,
        mock_add_comment: MagicMock,
    ) -> None:
        """Test handling command that raises exception."""
        mock_run.return_value = "[]"
        mock_parse.return_value = ("split", "abc1234-def5678")
        mock_cmd_split.side_effect = RuntimeError("test error")

        with patch.object(linecook_module.LineCook, "_initialize_remotes"):
            with patch.object(linecook_module.LineCook, "_check_labels_exist"):
                bot = linecook_module.LineCook(config=self.config, dry_run=True)

        bot.handle_command("#linecook split abc1234-def5678", 123)

        # Should add error comment
        mock_add_comment.assert_called_once()
        comment_text = mock_add_comment.call_args[0][1]
        self.assertIn("Failed to execute command", comment_text)
        self.assertIn("test error", comment_text)


if __name__ == "__main__":
    unittest.main()
