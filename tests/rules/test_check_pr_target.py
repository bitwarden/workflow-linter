"""Test src/bitwarden_workflow_linter/rules/check_pr_target."""

import pytest

from ruamel.yaml import YAML

from src.bitwarden_workflow_linter.load import WorkflowBuilder
from src.bitwarden_workflow_linter.rules.check_pr_target import (
    RuleCheckPrTarget,
)

yaml = YAML()
message = "Check-run job must be included when pull_request_target is used"

@pytest.fixture(name="correct_workflow")
def fixture_correct_workflow():
    workflow = """\
---
on:
  workflow_dispatch:
  pull_request_target:

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

@pytest.fixture(name="rule")
def fixture_rule():
    return RuleCheckPrTarget()

def test_rule_on_correct_workflow(rule, correct_workflow):
    obj = correct_workflow

    result, message = rule.fn(correct_workflow)
    assert result is True
    assert message == ""


def test_rule_on_no_checkworkflow(rule, no_check_workflow):
    obj = no_check_workflow

    result, message = rule.fn(no_check_workflow)
    assert result is False
    assert message == message

def test_rule_on_no_target_workflow(rule, no_target_workflow):
    obj = no_target_workflow

    result, message = rule.fn(no_target_workflow)
    assert result is True
    assert message == ""

def test_rule_on_jobs_without_needs(rule, no_needs_workflow):
    obj = no_needs_workflow

    result, message = rule.fn(no_needs_workflow)
    assert result is False
    assert message == message, "check-run is missing from the following jobs in the workflow: quality"