"""Test src/bitwarden_workflow_linter/rules/check_pr_target."""

import pytest

from ruamel.yaml import YAML
from unittest.mock import patch

from src.bitwarden_workflow_linter.load import WorkflowBuilder
from src.bitwarden_workflow_linter.rules.check_pr_target import (
    RuleCheckPrTarget,
)
from src.bitwarden_workflow_linter.models.workflow import Workflow
from src.bitwarden_workflow_linter.utils import Settings

yaml = YAML()
message = "A check-run job must be included as a direct job dependency when pull_request_target is used and the workflow may only apply to runs on the main branch"

@pytest.fixture(name="correct_workflow")
def fixture_correct_workflow():
    workflow = """\
---
on:
  workflow_dispatch:
  pull_request_target:
    types: [opened, synchronize]
    branches:
      - 'main'

jobs:
  check-run:
    name: Check PR run
    uses: bitwarden/gh-actions/.github/workflows/check-run.yml@main

  quality:
    name: Quality scan
    needs: check-run
    steps:
      - run: echo test

  dependent-job:
     name: Another Dependent Job
     needs:
       - quality
       - check-run
     steps:
       - run: echo another dependent job
"""
    return WorkflowBuilder.build(workflow=yaml.load(workflow), from_file=False)

@pytest.fixture(name="no_check_workflow")
def fixture_no_check_workflow():
    workflow = """\
---
on:
  workflow_dispatch:
  pull_request_target:
    types: [opened, synchronize]
    branches:
      - 'main'

jobs:
  job-key:
    runs-on: ubuntu-22.04
    steps:
      - run: echo test
"""
    return WorkflowBuilder.build(workflow=yaml.load(workflow), from_file=False)

@pytest.fixture(name="no_needs_workflow")
def fixture_no_needs_workflow():
    workflow = """\
---
on:
  workflow_dispatch:
  pull_request_target:
    types: [opened, synchronize]
    branches: main

jobs:
  check-run:
    name: Check PR run
    uses: bitwarden/gh-actions/.github/workflows/check-run.yml@main

  job-key:
    runs-on: ubuntu-22.04
    steps:
      - run: echo test

  quality:
    name: Quality scan
    steps:
      - run: echo test

"""
    return WorkflowBuilder.build(workflow=yaml.load(workflow), from_file=False)

@pytest.fixture(name="no_target_workflow")
def fixture_no_target_workflow():
    workflow = """\
---
on:
  workflow_dispatch:

jobs:
  job-key:
    runs-on: ubuntu-22.04
    steps:
      - run: echo test
"""
    return WorkflowBuilder.build(workflow=yaml.load(workflow), from_file=False)

@pytest.fixture(name="dependent_missing_check_workflow")
def dependent_missing_check_workflow():
    workflow = """\
---
on:
  workflow_dispatch:
  pull_request_target:
    types: [opened, synchronize]
    branches:
      - 'main'

jobs:
  check-run:
    name: Check PR run
    uses: bitwarden/gh-actions/.github/workflows/check-run.yml@main

  quality:
    name: Quality scan
    needs: check-run
    steps:
      - run: echo test

  dependent-job:
     name: Another Dependent Job
     needs:
       - quality
     steps:
       - run: echo another dependent job
"""
    return WorkflowBuilder.build(workflow=yaml.load(workflow), from_file=False)

@pytest.fixture(name="no_branches_workflow")
def fixture_no_branches_workflow():
    workflow = """\
---
on:
  workflow_dispatch:
  pull_request_target:
    types: [opened, synchronize]

jobs:
  check-run:
    name: Check PR run
    uses: bitwarden/gh-actions/.github/workflows/check-run.yml@main

  quality:
    name: Quality scan
    needs: check-run
    steps:
      - run: echo test

  dependent-job:
     name: Another Dependent Job
     needs:
       - quality
       - check-run
     steps:
       - run: echo another dependent job
"""
    return WorkflowBuilder.build(workflow=yaml.load(workflow), from_file=False)

@pytest.fixture(name="bad_branches_workflow")
def fixture_bad_branches_workflow():
    workflow = """\
---
on:
  workflow_dispatch:
  pull_request_target:
    types: [opened, synchronize]
    branches:
      - 'main'
      - 'not main'

jobs:
  check-run:
    name: Check PR run
    uses: bitwarden/gh-actions/.github/workflows/check-run.yml@main

  quality:
    name: Quality scan
    needs: check-run
    steps:
      - run: echo test

  dependent-job:
     name: Another Dependent Job
     needs:
       - quality
       - check-run
     steps:
       - run: echo another dependent job
"""
    return WorkflowBuilder.build(workflow=yaml.load(workflow), from_file=False)

@pytest.fixture(name="two_failures_workflow")
def fixture_two_failures_workflow():
    workflow = """\
---
on:
  workflow_dispatch:
  pull_request_target:
    types: [opened, synchronize]

jobs:
  check-run:
    name: Check PR run
    uses: bitwarden/some-other-repo/.github/workflows/check-run.yml@main

  quality:
    name: Quality scan
    needs: check-run
    steps:
      - run: echo test

  dependent-job:
     name: Another Dependent Job
     needs:
       - quality
       - check-run
     steps:
       - run: echo another dependent job
"""
    return WorkflowBuilder.build(workflow=yaml.load(workflow), from_file=False)

@pytest.fixture(name="rule")
def fixture_rule():
  settings= Settings(default_branch="main")
  return RuleCheckPrTarget(settings=settings)

@pytest.fixture
def mock_workflow():
    return Workflow(
        on={
            "pull_request_target": {
                "branches": ["main"]
            }
        },
        jobs={}
    )
def test_targets_main_branch_with_settings_yaml(mock_workflow):
    settings = Settings(default_branch="main")
    rule = RuleCheckPrTarget(settings=settings)
    assert rule.targets_main_branch(mock_workflow) is True

def test_targets_custom_default_branch(mock_workflow):
    settings = Settings(
        enabled_rules=[],
        approved_actions={},
        actionlint_version="",
        default_branch="production"
    )
    rule = RuleCheckPrTarget(settings=settings)
    mock_workflow.on["pull_request_target"]["branches"] = ["production"]
    assert rule.targets_main_branch(mock_workflow) is True

def test_targets_main_branch_no_default_branch(mock_workflow):
    # Mock the factory method to simulate loading default settings
    with patch("src.bitwarden_workflow_linter.utils.Settings.factory") as mock_factory:
        # Simulate the default settings returned by the factory
        mock_factory.return_value = Settings(default_branch="main")

        # Use the mocked factory to create the Settings instance
        settings = Settings.factory()
        rule = RuleCheckPrTarget(settings=settings)

        # Assert that the workflow targets the main branch
        assert rule.targets_main_branch(mock_workflow) is True

def test_targets_main_branch_incorrect_branch(mock_workflow):
    settings = Settings({"default_branch": "main"})
    rule = RuleCheckPrTarget(settings=settings)
    mock_workflow.on["pull_request_target"]["branches"] = ["feature"]
    assert rule.targets_main_branch(mock_workflow) is False

def test_targets_main_branch_no_branches_specified(mock_workflow):
    settings = Settings({"default_branch": "main"})
    rule = RuleCheckPrTarget(settings=settings)
    mock_workflow.on["pull_request_target"].pop("branches")
    assert rule.targets_main_branch(mock_workflow) is False

def test_rule_on_correct_workflow(rule, correct_workflow):
    result, message = rule.fn(correct_workflow)
    assert result is True
    assert message == ""

def test_rule_on_no_checkworkflow(rule, no_check_workflow):
    result, message = rule.fn(no_check_workflow)
    assert result is False
    assert message == message

def test_rule_on_no_target_workflow(rule, no_target_workflow):
    result, message = rule.fn(no_target_workflow)
    assert result is True
    assert message == ""

def test_rule_on_jobs_without_needs(rule, no_needs_workflow):
    result, message = rule.fn(no_needs_workflow)
    assert result is False
    assert message == message, "check-run is missing from the following jobs in the workflow: quality"

def test_rule_on_dependencies_without_check(rule, dependent_missing_check_workflow):
    result, message = rule.fn(dependent_missing_check_workflow)
    assert result is False
    assert message == message, "check-run is missing from the following jobs in the workflow: dependent-job"

def test_rule_on_no_branches_workflow(rule, no_branches_workflow):
    result, message = rule.fn(no_branches_workflow)
    assert result is False
    assert message == "Workflows using pull_request_target can only target the 'main' branch"

def test_rule_on_only_target_main(rule, bad_branches_workflow):
    result, message = rule.fn(bad_branches_workflow)
    assert result is False
    assert message == "Workflows using pull_request_target can only target the 'main' branch"

def test_rule_on_two_failures(rule, two_failures_workflow):
    result, message = rule.fn(two_failures_workflow)
    assert result is False
    assert message == "Workflows using pull_request_target can only target the 'main' branch\nA check-run job must be included as a direct job dependency when pull_request_target is used"
