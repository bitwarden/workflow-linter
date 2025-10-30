# Bitwarden Workflow Linter - Claude Instructions

## Repository Overview

**Bitwarden Workflow Linter** is an extensible Python CLI tool that enforces opinionated organization-specific GitHub Action standards.

**CRITICAL UNDERSTANDING**: This tool generates and publishes **rules that are consumed across ALL Bitwarden repositories**. Changes to rules affect the entire Bitwarden organization's CI/CD pipelines, not just this repository. Rules are distributed via PyPI and consumed by repositories through the [composite Action](https://github.com/bitwarden/gh-actions/tree/main/lint-workflow).

### High-Level Details

-   **Type**: Python CLI application and library (~86 Python files)
-   **Language**: Python 3.13.5 (minimum 3.11 supported)
-   **Package Manager**: pipenv for dependencies, hatch for building/publishing
-   **Distribution**: Published to PyPI as `bitwarden_workflow_linter`
-   **CLI Command**: `bwwl`
-   **Organizational Impact**: Rules affect CI/CD across entire Bitwarden codebase

## Build & Development Setup

### Essential Commands (Always run in this order)

```bash
# Setup (REQUIRED before any development work)
pipenv install --dev
pipenv shell
pip install -e .

# Testing (ALWAYS run before submitting changes)
pytest tests --cov=src

# Code quality (REQUIRED before merging to main)
black .
pylint --rcfile pylintrc src/ tests/

# Type checking (Linux only)
pytype src
```

### Task Runner Shortcuts

-   `task test:cov` - Run tests with coverage
-   `task fmt` - Format code with black
-   `task lint` - Run pylint

## Key Project Structure

**Rules Location**: `src/bitwarden_workflow_linter/rules/` - All linting rules
**Rule Base Class**: `src/bitwarden_workflow_linter/rule.py` - Extend this for new rules
**CLI Entry**: `src/bitwarden_workflow_linter/cli.py:main()`
**Configuration**:

-   `settings.yaml` (local overrides)
-   `src/bitwarden_workflow_linter/default_settings.yaml` (defaults)

## Rule Development - Organization-Wide Impact

**CRITICAL**: Rules developed here are distributed to and enforced across ALL Bitwarden repositories. Every rule change has organization-wide impact.

### Rule Distribution Flow

1. Rules developed/tested in this repository
2. Published to PyPI as `bitwarden_workflow_linter`
3. Consumed by all Bitwarden repositories via gh-actions/lint-workflow
4. Enforced in CI/CD pipelines organization-wide
5. Rule failures can block deployments across hundreds of repositories

### Rule Rollout Process (MANDATORY)

**Before making ANY rule changes, read `RULE_ROLLOUT.md`** - documents the careful process for organization-wide deployment.

**Key principles:**

-   **Gradual Rollout**: New rules start as `warning`, then upgrade to `error`
-   **Impact Assessment**: Test against representative workflows before activation
-   **Communication**: Coordinate with teams before deploying breaking changes

### Adding New Rules

1. **CRITICAL**: Rules must be implemented, tested, and merged to main BEFORE activation
2. **CRITICAL**: Follow `RULE_ROLLOUT.md` process to avoid breaking organization CI
3. Extend `Rule` base class in `src/bitwarden_workflow_linter/rule.py`
4. Place in `src/bitwarden_workflow_linter/rules/`
5. Must define: `message`, `on_fail`, `compatibility`, `settings`, and `fn()` method
6. Add comprehensive tests with 100% coverage
7. Start with `warning` level, upgrade to `error` after validation period
8. After release, activate by adding to `settings.yaml` and `default_settings.yaml`

### Rule Impact Levels

-   **ERROR Level**: Block CI/CD across all Bitwarden repositories - handle with extreme care
-   **WARNING Level**: Generate notifications but don't block - safer for initial rollout

## Security Considerations

### Critical Security Rules (Organization-Wide)

-   **Action Pinning**: `step_pinned.py` enforces SHA pinning (not tags) at ERROR level across all repos
    -   Example: `uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2`
-   **Approved Actions**: `step_approved.py` enforces use of pre-approved actions only
-   **Permissions**: `permissions_exist.py` enforces explicit permissions in workflows
-   **PR Target Protection**: `check_pr_target.py` prevents dangerous `pull_request_target` usage

**Security rule changes affect organization-wide security posture - always coordinate with security team.**

## Critical Issues & Solutions

### Rule Activation Order

-   **ERROR**: Activating rules before release causes import errors across all Bitwarden repositories
-   **SOLUTION**: Always merge rule implementation first, then activate after PyPI release

### Organization-Wide Impact

-   **ERROR**: Deploying ERROR-level rules without testing breaks CI across hundreds of repositories
-   **SOLUTION**: Start with WARNING level, test extensively, coordinate rollout via `RULE_ROLLOUT.md`

### Testing Best Practices

-   Tests change directories to avoid repo-specific paths
-   Use `default_settings.yaml` instead of repo `settings.yaml` in tests
-   Run with `--strict` flag to catch warnings as errors
-   Test rules against diverse workflow patterns from different Bitwarden repositories

## Agent Instructions

**Trust these instructions first** - only search for additional information if incomplete or incorrect.

**CRITICAL AWARENESS**: This repository's rules are consumed across ALL Bitwarden repositories. Every change has organization-wide impact.

**Required sequence for changes:**

1. **Read `RULE_ROLLOUT.md` if working with rules** - understand organization-wide impact
2. `pipenv shell && pip install -e .`
3. `pytest tests --cov=src`
4. `black . && pylint --rcfile pylintrc src/ tests/`
5. Test CLI: `bwwl lint --files tests/fixtures`

**For rule development:**

-   Rules affect hundreds of other Bitwarden repositories
-   Start with WARNING level, coordinate rollout, upgrade to ERROR only after validation
-   **Never deploy ERROR-level rules without extensive testing and coordination**
