# Line Cook

[![Lint](https://github.com/jaymzh/line-cook/actions/workflows/lint.yml/badge.svg)](https://github.com/jaymzh/line-cook/actions/workflows/lint.yml)
[![Unit Tests](https://github.com/jaymzh/line-cook/actions/workflows/unit.yml/badge.svg)](https://github.com/jaymzh/line-cook/actions/workflows/unit.yml)

Line cook is an automated bot for syncing upstream Facebook Chef cookbooks to
your downstream repo and managing pull requests. Works with both the primary
Facebook repo as well as UNIVERSE repos. Think of it as Dependabot, but for
FB-style Chef cookbooks.

Since the model avoids versions, this uses a model similar to
[ShipIt](https://github.com/facebookarchive/fbshipit) to walk commits and sync
them. It will make a PR with a list of cherry-picked commits relevant to your
cookbooks to get you up-to-date.

Like Dependabot, it has highly configurable as well as accepts commands via
comments on its PRs.

It has a variety of features, but the high level ones are:

- **Automatically syncs** commits from the upstream repository
- **Creates PRs** with detailed commit information and trailers
- **Detects conflicts** and creates GitHub issues for cookbooks with local
  changes
- **Supports interactive commands** for PR management (split, rebase)
- **Provides feedback** via PR/issue comments on command success or failure

See some examples:

- [Sample PR with upstream
  updates](https://github.com/socallinuxexpo/scale-chef/pull/563)
- [Sample Issue with sync
  conflicts](https://github.com/socallinuxexpo/scale-chef/issues/554)
- [Sample Issue with pending local changes to be pushed
  upstream](https://github.com/socallinuxexpo/scale-chef/issues/562)

## How It Works

The bot runs in two modes:

1. **Sync Mode** (scheduled/triggered): Fetches upstream commits and
   creates/updates sync PRs
1. **Command Mode** (comment-triggered): Responds to commands on PRs to split
   or rebase them

The bot supports syncing from **multiple upstream repositories**
simultaneously, with each upstream identified by a cookbook prefix (e.g.,
`fb`, `pd`). Cookbooks are named with the prefix followed by an underscore
(e.g., `fb_apache`, `pd_nginx`). Each upstream is tracked independently with
its own commit trailers, PRs, and issues.

### Sync Process

1. Fetches latest commits from all configured upstream repositories
1. For each upstream:
   - Identifies which commits haven't been synced yet (using upstream-specific
     trailers)
   - Attempts to cherry-pick each commit with the appropriate trailer
   - Creates/updates PRs for successfully synced commits
   - Creates GitHub issues for cookbooks with conflicts or local changes
1. Each upstream gets its own sync PR branch and is processed independently

### Command Process

1. Monitors PR comments for bot commands (tag is configurable, default:
   `#linecook`)
1. Automatically detects which upstream a PR belongs to based on branch name or
   trailers
1. Parses and validates the command
1. Executes the requested operation (split or rebase)
1. Posts success/failure feedback as a PR comment

## Configuration

### Bot Configuration File

Create a `line-cook.yml` file in your repository root. See
[`line-cook.yml`](examples/line-cook.yml) for a complete annotated
example.

The defaults are designed to work out of the box, but many people may wish
to customize the labels and command tag that Line Cook uses.

**Important Notes:**

- **Automatic Remote Management**: The bot automatically initializes git
  remotes for all configured upstreams using the pattern `{prefix}_upstream`
  (e.g., `fb_upstream`, `pd_upstream`). You don't need to manually set up
  remotes.
- **Unique Prefixes Required**: Each upstream must have a unique prefix. The
  bot validates this on startup and will fail if duplicates are found. Prefixes
  are specified without the trailing underscore in the config (e.g., `prefix: pd`),
  but the bot automatically adds the underscore when matching cookbooks.
- **Commit Trailers**: Each upstream uses its own trailer key for tracking:
   - Primary upstream (typically `fb`): uses `Upstream-Commit`
   - Other upstreams: use `{prefix}_Upstream-Commit` (e.g., `pd_Upstream-Commit`)
- **Separate PRs**: Each upstream gets its own sync PR with a branch name like
  `line-cook/{prefix}_/update` (e.g., `line-cook/fb_/update`, `line-cook/pd_/update`)

## Running manually

When setting things up, it may be helpful to run the bot manually
instead of through a workflow. If you use a fork-based setup, you'll
want to override the default target remote, and you'll want to run in
dry-run mode, like so:

```bash
# from your repo....
path/to/line-cook/bin/line-cook.py --dry-run --target-remote upstream
```

Note that you will not end up on the same branch, as the bot will
change branches to do work, so when iterating, it's easiest to make
sure your command line is always checking out the branch you want it
to work from:

```bash
git checkout main; path/to/line-cook/bin/line-cook.py --dry-run --target-remote upstream
```

Starting from a different branch won't change where Line Cook syncs
from, that's part of it's configuration - however, if your working
branch is what has it's config file, you'll need to execute it from
that branch for it to be effective.

Where you set `--target-remote` to whatever remote is the _target_ for
your pull requests.

## Initial Setup & Onboarding

Until you get the hang of Line Cook, we recommend running it in dry-run mode
from the command line as described in the section above. You can then run it
regular mode. Once you're comfortable, you can setup the workflows.

Start with creating your config file, the fire it off.

### Bootstrapping Mode

Upon first run, Line Cook will detect that a repo doesn't have a baseline and
will attempt to do some bootstrapping.

In bootstrapping mode it'll attempt to find a "baseline" for each cookbook in
your repo that comes from a given upstream. A baseline is an upstream commit
that has a commit in your repo where the content matches - i.e. it attempts to
figure out what upstream commit you copied that cookbook from.

_IF_ it can find a baseline for all cookbooks, then it'll use the latest common
ancestor commit for all of the baselines as your new "global baseline" and
create a Pull Request that denotes that SHA. Once this is PR is merged, then
Line Cook can start making sync PRs.

_If it cannot_ find a basline for all cookbooks, it'll try to create a "Fixup
PR" for the cookbooks where a baseline could not be determined. This is done by
finding the ancestor for all the cookbooks for which a baseline was determined
and then try to making a Pull Request which will sync all of the "missing
baseline cookbooks" to that SHA.

While a "Fixup PR" exists, it will not attempt to create a "Bootstrap PR." Once
the F"Fixup PR" is merged (or close), the next run will attempt again to
boostrap.

Once you have a boostrap PR merged, you're off to the races.

If you ever add a new upstream (a UNIVERSE repo), the normal sync mode will
enter bootstrapping mode for that upstream, but do normal syncing for any other
upstreams.

### Force Bootstrap

If you need to reset the baseline for an upstream, you can use the
`--force-bootstrap` flag, by running it manually on the command line. This
will re-detect the baseline and create a new onboarding PR.

### Forcing fix up mode

Like with bootstrap, you can force creating fix-up PRs even post bootstrapping
with `--fix-missing-baselines`.

## Workflow Setup

The bot requires two GitHub Actions workflows in your repository.

### 1. Upstream Sync Workflow

This is the primary workflow that runs the sync process.

Create `.github/workflows/line-cook-sync.yml` - see
[line-cook-sync.yml](examples/workflows/line-cook-sync.yml) for a complete
annotated example.

**Workflow Inputs:**

- `base_branch`: Your repository branch (default: from config or `main`)
- `pr_branch_prefix`: Prefix for automated PR branches (default: from
  config or `line-cook`)
- `python_version`: Python version to use (default: `3.11`)
- `dry_run`: If true, only logs actions without making changes
  (default: `false`)

Note that `base_branch` and `pr_branch_prefix` can be configured in
your `line-cook.yml` file. Workflow inputs override the config file
values.

The following optional inputs exist for testing with a different
branch of line cook:

- `line_cook_repository`: The repository containing the line cook code to use
  (default: `jaymzh/line-cook`)
- `line_cook_repo_ref`: The git ref (branch, tag, or commit) of the line cook
  repository to use (default: `main`)
- `line_cook_path`: The path within the repository to the line cook code
  (default: `bin/line-cook.py`)

### 2. Command Handler Workflow

This is the workflow that listens for commands in PR comments and executes
them. Create `.github/workflows/line-cook-commands.yml` - see
[line-cook-commands.yml](examples/workflows/line-cook-commands.yml) for a
complete annotated example.

## Bot Commands

Comment on any Line Cook PR with these commands. The bot automatically detects
which upstream the PR belongs to based on the branch name and commit trailers,
so commands work seamlessly across multiple upstreams.

### Split Command

Split a PR into two separate PRs. Use this when you want to merge part of a
sync PR while keeping the rest for later.

**Syntax:**

```text
#linecook split <start-sha>-<end-sha>
```

**Parameters:**

- `start-sha`: First 7-40 characters of the starting commit SHA
- `end-sha`: First 7-40 characters of the ending commit SHA

**Requirements:**

- The range must be contiguous from one end of the PR (beginning or end), not
  from the middle
- The SHAs must exist in the PR's `Upstream-Commit` trailers

**Example:**

```text
#bot split abc1234-def5678
```

**What happens:**

1. The original PR is rewritten to contain only the specified range of commits
1. A new PR is created with the remaining commits
1. Both PRs are labeled with the `split_label` from your config
1. A success comment is posted with details

**Success Response:**

```text
✅ Split completed successfully!

- Updated this PR with 3 commit(s)
- Created new PR #123 with 5 commit(s)
```

### Rebase Command

Rebase the PR onto the latest base branch. Use this when the base branch has
moved ahead and you want to update the PR.

**Syntax:**

```text
#linecook rebase
```

**What happens:**

1. Fetches the latest base branch
1. Rebases the PR branch onto it
1. Force-pushes the rebased branch (using `--force-with-lease` for safety)
1. Posts a success comment

**Success Response:**

```text
✅ Rebase completed successfully!

- Rebased 8 commit(s) onto latest `main`
- Branch `line-cook/abc1234` has been updated
```

**Conflict Handling:**
If the rebase encounters conflicts, the bot posts an error comment with manual
resolution instructions:

```text
❌ Failed to execute command `rebase`

**Error:** Rebase failed with conflicts. Please resolve conflicts manually.
You may need to checkout the branch locally and run:

git checkout line-cook/abc1234
git rebase origin/main
# Resolve conflicts
git rebase --continue
git push --force-with-lease
```

### Unknown Command Response

If you use an unrecognized command, the bot responds with:

```text
❌ Unknown command: `yourcommand`

Supported commands:
- `#bot split <sha1>-<sha2>` - Split a PR into two PRs
- `#bot rebase` - Rebase the PR onto the latest base branch
```

## PR Structure

Sync PRs created by the bot have a specific structure:

The title will be:

```text
Sync upstream (N commits)
```

The body will be:

```markdown
Syncing upstream commits. The PRs are listed below. You can comment in this PR
with commands see below. Also, this description is build for squash-merge, make
sure you keep all the `Upstream-Commit` trailers in tact.

* cookbook_name: Short commit description
  * Upstream-Commit: abc123...

* another_cookbook: Another commit description
  * Upstream-Commit: def456...
```

Followed by a list of commands you can issue the bot in comments.

**Commit Trailers:**

The trailers are critical for tracking which upstream commits have been synced.
You must ensure these tags stay in the commit message when the PR is merged.

- **Primary upstream** (typically `fb` prefix): uses `Upstream-Commit`
- **Other upstreams**: use `{prefix}_Upstream-Commit` (e.g.,
  `pd_Upstream-Commit`)

**Multiple Upstreams:**

When syncing from multiple upstreams, each upstream gets its own separate PR:

- Branch name: `line-cook/{prefix}_/update` (e.g., `line-cook/fb_/update`,
  `line-cook/pd_/update`)
- Each PR only contains commits for cookbooks with that upstream's prefix
- Trailers use the upstream-specific format to avoid conflicts

## GitHub Issues

The bot creates GitHub issues when it detects:

1. **Sync conflicts**: When cherry-picking upstream commits fails
1. **Local changes**: When cookbooks have been modified locally

Issues include:

- Commit SHA that caused the conflict
- Affected cookbooks
- Conflict details (if available)
- Required actions

Issues are automatically labeled with `bot_label` from your config. When
syncing from multiple upstreams, issue titles will indicate which upstream is
affected.

## Permissions

The bot requires the following GitHub permissions:

- **Contents**: Write (to create branches and push commits)
- **Pull Requests**: Write (to create and manage PRs)
- **Issues**: Write (to create conflict issues)

These are provided by the `GITHUB_TOKEN` secret in GitHub Actions, which is
automatically available.

## Dry Run Mode

Test the bot without making actual changes by setting `dry_run: true` in the
workflow:

```yaml
with:
  dry_run: true
```

In dry-run mode:

- No (remote) branches are created or pushed
- No PRs are created
- No issues are filed
- No comments are posted
- All actions are logged with `[dry-run]` prefix

This is useful for testing bot changes in PRs before merging to main.

## FAQ & Troubleshooting

### How do I sync from multiple upstream repositories

Add additional upstreams to the `universe_upstreams` section of your
`line-cook.yml`. Each upstream must have:

- A unique `prefix` that matches your cookbook naming convention
- A `repo_url` pointing to the upstream repository
- Optionally, a `branch` (defaults to `main`) and `ignore_cookbooks` list

The bot will automatically:

- Create and manage git remotes for each upstream
- Generate separate sync PRs for each upstream
- Track commits independently using prefix-specific trailers

### What if I already have git remotes set up

The bot validates existing remotes on startup. If a remote with the expected
name already exists, it checks that the URL matches your configuration. If
there's a mismatch, the bot will fail with an error message asking you to fix
the remote URL manually.

### Can I have cookbooks from different upstreams in the same repository

Yes! That's the primary use case for multi-upstream support. Each cookbook is
identified by its prefix (e.g., `fb_apache`, `pd_nginx`), and the bot syncs
them from their respective upstream repositories independently.

### What happens if two upstreams have the same cookbook name

Upstreams must have unique prefixes specifically to avoid this. Cookbooks are
identified by their full name including the prefix. If you have `fb_apache` and
`pd_apache`, they're treated as completely separate cookbooks.

### How do I remove an upstream

Simply remove it from your `line-cook.yml` configuration. The bot will
stop syncing from that upstream on the next run. The git remote will remain
(the bot doesn't delete remotes), but it won't be used. You can manually remove
it with `git remote remove <remote-name>` if desired.

### Can I temporarily disable syncing for one upstream

Yes, you can:

1. Comment out or remove that upstream from `universe_upstreams`
1. Or add all its cookbooks to `ignore_cookbooks` for that upstream

The first approach is cleaner if you want to completely pause syncing.
