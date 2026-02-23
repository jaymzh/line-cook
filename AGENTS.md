# AGENTS.md

This document provides guidance for AI coding agents working with the
Line Cook codebase.

## Project Overview

Line Cook is a GitHub Actions-based bot that automates syncing Chef
cookbooks from upstream repositories (primarily Facebook's
chef-cookbooks) to downstream forks. It manages pull requests, handles
conflicts, creates issues for problematic cookbooks, and responds to
commands on PRs.

### Key Features

1. Multi-upstream support with independent tracking per upstream
1. Automatic PR creation for synced commits
1. Conflict detection and GitHub issue creation
1. Interactive commands for PR management (split, rebase)
1. Onboarding mode for initial setup

### Technology Stack

- **Language**: Python 3 (3.11+)
- **Dependencies**: PyYAML, black (for code formatting)
- **External Tools**: Git, GitHub CLI (`gh`)
- **Platform**: GitHub Actions (Linux runners)

## Code Style and Conventions

### Line Length

**CRITICAL**: All code and comments must be kept to **< 80 characters
wide**. This is a strict requirement. Break lines appropriately to
maintain readability while staying within this limit.

Examples from the codebase:

```python
# Good - under 80 chars
def upstream_commits_since(
    self, pointer: Optional[str], upstream_config: Dict
) -> List[str]:

# Function calls split across lines
output = run(
    [
        "gh",
        "pr",
        "list",
        "--base",
        self.base_branch,
    ]
)
```

### Markdown Formatting

When creating numbered lists in Markdown files (including this one),
**always use "1" for all items** rather than sequential numbering:

```markdown
1. First item
1. Second item
1. Third item
```

This allows for easier reordering and better diffs. The Markdown
renderer will display them as 1, 2, 3, etc.

### Python Code Style

1. **Type Hints**: Use type hints for all function parameters and
   return values

   ```python
   def load_config() -> Dict:
   def try_git(*args: str) -> Tuple[bool, str, str]:
   ```

1. **Docstrings**: All functions and classes should have docstrings
   with Args/Returns sections

   ```python
   """
   Get list of upstream commits since the given pointer.

   Args:
       pointer: Starting commit SHA (exclusive)
       upstream_config: Upstream configuration dict

   Returns:
       List of commit SHAs
   """
   ```

1. **Logging**: Use the module logger for all logging, with
   appropriate levels (debug, info, warning, error)

   ```python
   logger = logging.getLogger(__name__)
   logger.debug(f"Found {len(commits)} upstream commits")
   logger.info(f"Fetching upstream from remote: {remote}")
   logger.warning(f"Could not determine upstream from PR")
   logger.error(f"Command failed: {' '.join(cmd)}")
   ```

1. **F-strings**: Prefer f-strings for string formatting

   ```python
   f"Remote '{remote_name}' exists with URL '{existing_url}'"
   ```

1. **Dict/List Trailing Commas**: Use trailing commas in multi-line
   dicts and lists

   ```python
   default_config = {
       "bot_label": "line-cook",
       "split_label": "line-cook-pr-split",
       "bot_command_prefix": "#linecook",
   }
   ```

1. **Black Formatting**: Code is formatted with `black==25.12.0`.
   Run black after making changes.

## Architecture

### Main Components

1. **Configuration System** (`load_config()`): Loads and validates
   YAML configuration from `line-cook.yaml`

1. **LineCook Class**: Main bot logic with two primary modes:
   - Sync mode: Fetch upstream commits and create/update PRs
   - Command mode: Process bot commands from PR comments

1. **Multi-Upstream Support**: Each upstream has:
   - Unique prefix (e.g., `fb`, `pd`) specified in config without
     trailing underscore
   - Dedicated git remote (`{prefix}_upstream`, e.g., `fb_upstream`)
   - Own trailer key for commit tracking (`{prefix}_Upstream-Commit`)
   - Independent PR and issue management

1. **Git Utilities**: Helper functions for git operations
   - `git()`: Run git commands that must succeed
   - `try_git()`: Run git commands that may fail
   - `run()`: Generic command execution

### Key Data Structures

**Upstream Config Dict**:

```python
{
    "prefix": "fb",
    "repo_url": "https://github.com/...",
    "remote": "fb_upstream",
    "branch": "main",
    "ignore_cookbooks": ["fb_init"],
    "is_primary": True,
    "trailer_key": "Upstream-Commit",
}
```

**Bot Config Dict**:

```python
{
    "bot_label": "line-cook",
    "split_label": "line-cook-pr-split",
    "bot_command_prefix": "#linecook",
    "upstream_overrides": {...},
    "universe_upstreams": {...},
}
```

### Important Patterns

1. **Dry Run Support**: Most operations support dry-run mode via
   `self.dry_run` flag

1. **Upstream Detection**: Multiple methods to determine which
   upstream a PR/commit/cookbook belongs to:
   - `_determine_upstream_from_pr()`: From branch name or trailers
   - `_get_upstream_for_cookbook()`: From cookbook prefix
   - `_get_upstream_for_commit()`: From files touched

1. **Trailer Tracking**: Git commit trailers track upstream commits:
   - Primary upstream: `Upstream-Commit: <sha>`
   - Other upstreams: `{prefix}Upstream-Commit: <sha>`

1. **Error Handling**: Command failures raise `RuntimeError`, logging
   stderr for debugging

## File Structure

```text
line-cook/
├── bin/
│   └── line-cook.py          # Main bot implementation (2876 lines)
├── examples/
│   ├── line-cook.yml         # Configuration example
│   └── workflows/
│       ├── line-cook-sync.yml      # Sync workflow
│       └── line-cook-commands.yml  # Command workflow
├── requirements.txt          # Python dependencies
├── README.md                 # User documentation
├── AGENTS.md                 # This file
└── LICENSE                   # Apache 2.0 license
```

## Development Guidelines

### Making Changes

1. **Read Context First**: The bot is a single 2876-line Python file.
   Read relevant sections before making changes.

1. **Test Locally**: Use dry-run mode to test changes:

   ```bash
   ./bin/line-cook.py --dry-run
   ```

1. **Format Code**: Run black before committing:

   ```bash
   black bin/line-cook.py
   ```

1. **Update Documentation**: Update README.md if user-facing changes
   are made

1. **Write Tests**: Add unit tests for all new functionality (see
   Testing section below)

### Testing Requirements

**CRITICAL**: All new functionality must include unit tests.

When implementing new features:

1. Add tests to the appropriate file in `tests/` directory:
   - `test_commands.py`: Command parsing and handling
   - `test_config.py`: Configuration loading and validation
   - `test_git_utils.py`: Git utility functions
   - `test_pr_management.py`: PR and issue operations
   - `test_upstream.py`: Upstream detection and management
1. Create a new test file if functionality doesn't fit existing
   categories
1. Mock external dependencies (git, gh CLI, file system)
1. Test both success and failure scenarios
1. Test with multiple upstream configurations where applicable

Run tests before committing:

```bash
pytest tests/
```

### Common Tasks

**Adding a New Command**:

1. Add command parsing logic to `_parse_command()`
1. Implement command handler method
1. Update `handle_command()` to route to new handler
1. **Add tests** to `test_commands.py` for parsing and handling
1. Add user documentation to README.md

**Adding Upstream Configuration**:

1. Update `_setup_upstreams()` if new config options needed
1. Update `_validate_config()` for validation
1. **Add tests** to `test_config.py` for validation
1. Update example `line-cook.yml`

**Modifying Git Operations**:

1. Use `git()` for operations that must succeed
1. Use `try_git()` for operations that may fail
1. **Always use `-s` flag with `git commit`** to add sign-off
1. Log at appropriate levels (debug for details, info for milestones)
1. Handle both dry-run and normal execution paths
1. **Add tests** to `test_git_utils.py` or appropriate test module

**Adding New Core Features**:

1. Follow code style guidelines (< 80 char lines, type hints,
   docstrings)
1. Support dry-run mode where applicable
1. Consider multi-upstream scenarios
1. Add appropriate logging
1. **Write unit tests** before or alongside implementation
1. Update documentation (README.md, AGENTS.md, config examples)

## Testing

### Manual Testing

1. **Configuration Validation**:

   ```bash
   ./bin/line-cook.py --dry-run sync
   ```

1. **Command Parsing**:
   Test with various PR comment scenarios

1. **Multi-Upstream**:
   Test with multiple upstreams configured

### GitHub Actions Testing

1. PR-based dry-run testing is automatic (see workflows)
1. Test both sync and command workflows
1. Verify concurrency handling

## Common Pitfalls

1. **Line Length**: Easy to exceed 80 chars with long strings or
   function calls. Break lines early.

1. **Upstream Detection**: When adding features, consider multi-
   upstream scenarios. Don't assume single upstream.

1. **Dry Run Mode**: New features must respect `self.dry_run` flag
   for GitHub Actions PR testing.

1. **Git Remote State**: The bot manages git remotes automatically.
   Don't assume remotes exist or have specific URLs.

1. **Trailer Keys**: Primary upstream uses "Upstream-Commit", others
   use "{prefix}_Upstream-Commit" (e.g., "pd_Upstream-Commit"). Note that
   prefixes are configured without trailing underscore but the underscore is
   added when creating remote names, trailer keys, branch names, and when
   matching cookbooks. Don't hardcode.

1. **Labels**: Bot requires specific labels to exist. Verify in
   `_check_labels_exist()` when adding new label usage.

## Configuration Options

The bot uses configuration from `line-cook.yml` with command-line
overrides:

**Config File Options:**

- `base_branch`: Target branch for PRs (default: "main")
- `pr_branch_prefix`: Prefix for PR branches (default: "line-cook")
- `bot_label`: Label for bot-created PRs/issues
- `split_label`: Label for split PRs
- `bot_command_prefix`: Command prefix in PR comments
- `upstream_overrides`: Override primary upstream settings
- `universe_upstreams`: Additional upstream repositories

**Command-Line Options:**

- `--base-branch`: Override config base_branch
- `--pr-branch-prefix`: Override config pr_branch_prefix
- `--target-remote`: Git remote to push to (default: "origin")
- `--dry-run`: Don't push branches, PRs, or file issues
- `--force-bootstrapping`: Ignore current upstream pointer
- `--fix-missing-baselines`: Fix cookbooks without baselines

**Environment Variables:**

- `GITHUB_EVENT_NAME`: GitHub Actions event type
- `GITHUB_EVENT_PATH`: Path to GitHub event payload
- `GITHUB_TOKEN`: GitHub API authentication (required for gh CLI)
- `GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL`: Git commit author info
- `GIT_COMMITTER_NAME`, `GIT_COMMITTER_EMAIL`: Git committer info

## Useful References

- Main documentation: [README.md](README.md)
- Configuration example: [examples/line-cook.yml](examples/line-cook.yml)
- GitHub Actions workflows: `examples/workflows/`
- Python logging: Uses built-in `logging` module
- GitHub CLI: Requires `gh` tool for API operations

## Questions or Issues?

When encountering issues:

1. Check the logs - the bot logs extensively at debug level
1. Verify configuration with `--dry-run`
1. Test git operations manually to isolate issues
1. Review recent changes to identify regressions
1. Check GitHub Actions logs for workflow issues
