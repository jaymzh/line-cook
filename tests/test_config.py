#!/usr/bin/env python3
"""Tests for configuration loading and validation."""

import unittest
from unittest.mock import patch, mock_open, MagicMock
import tempfile
import os
import sys
from pathlib import Path

# Add bin to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))

# Import after path setup
import yaml

# Use dynamic import to avoid type checking issues
linecook = __import__("line-cook")


class TestConfigLoading(unittest.TestCase):
    """Test configuration loading."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.default_config = {
            "bot_label": "line-cook",
            "split_label": "line-cook-pr-split",
            "bot_command_prefix": "#linecook",
            "base_branch": "main",
            "pr_branch_prefix": "line-cook",
            "upstream_overrides": {
                "prefix": "fb",
                "repo_url": (
                    "https://www.github.com/facebook/" "chef-cookbooks.git"
                ),
                "ignore_cookbooks": ["fb_init", "fb_init_sample"],
            },
            "universe_upstreams": {},
        }

    def test_load_config_no_file(self) -> None:
        """Test loading config when file doesn't exist."""
        with patch("pathlib.Path.exists", return_value=False):
            config = linecook.load_config()
            self.assertEqual(
                config["bot_label"], self.default_config["bot_label"]
            )
            self.assertEqual(
                config["split_label"], self.default_config["split_label"]
            )

    def test_load_config_with_file(self) -> None:
        """Test loading config from YAML file."""
        test_config = {
            "bot_label": "custom-bot",
            "split_label": "custom-split",
            "bot_command_prefix": "#custom",
        }
        yaml_content = yaml.dump(test_config)

        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=yaml_content)):
                config = linecook.load_config()
                self.assertEqual(config["bot_label"], "custom-bot")
                self.assertEqual(config["split_label"], "custom-split")
                self.assertEqual(config["bot_command_prefix"], "#custom")

    def test_load_config_with_universe_upstreams(self) -> None:
        """Test loading config with universe upstreams."""
        test_config = {
            "universe_upstreams": {
                "pd-cookbooks": {
                    "prefix": "pd",
                    "repo_url": "https://github.com/test/repo.git",
                }
            }
        }
        yaml_content = yaml.dump(test_config)

        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=yaml_content)):
                config = linecook.load_config()
                self.assertIn("pd-cookbooks", config["universe_upstreams"])
                self.assertEqual(
                    config["universe_upstreams"]["pd-cookbooks"]["prefix"],
                    "pd",
                )


class TestConfigValidation(unittest.TestCase):
    """Test configuration validation."""

    def test_validate_duplicate_prefixes(self) -> None:
        """Test validation catches duplicate prefixes."""
        config = {
            "upstream_overrides": {"prefix": "fb"},
            "universe_upstreams": {
                "test": {"prefix": "fb", "repo_url": "test.git"}
            },
        }
        with self.assertRaises(ValueError) as ctx:
            linecook._validate_config(config)
        self.assertIn("Duplicate", str(ctx.exception))

    def test_validate_missing_prefix(self) -> None:
        """Test validation catches missing prefix."""
        config = {
            "universe_upstreams": {
                "test": {"repo_url": "test.git"}  # Missing prefix
            }
        }
        with self.assertRaises(ValueError) as ctx:
            linecook._validate_config(config)
        self.assertIn("missing required 'prefix'", str(ctx.exception))

    def test_validate_missing_repo_url(self) -> None:
        """Test validation catches missing repo_url."""
        config = {
            "universe_upstreams": {
                "test": {"prefix": "test"}  # Missing repo_url
            }
        }
        with self.assertRaises(ValueError) as ctx:
            linecook._validate_config(config)
        self.assertIn("missing required 'repo_url'", str(ctx.exception))

    def test_validate_valid_config(self) -> None:
        """Test validation passes for valid config."""
        config = {
            "upstream_overrides": {"prefix": "fb"},
            "universe_upstreams": {
                "test": {"prefix": "pd", "repo_url": "test.git"}
            },
        }
        # Should not raise
        linecook._validate_config(config)


if __name__ == "__main__":
    unittest.main()
