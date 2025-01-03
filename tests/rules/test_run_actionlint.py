"""Test src/bitwarden_workflow_linter/rules/run_actionlint."""

import pytest

from ruamel.yaml import YAML

from src.bitwarden_workflow_linter.load import WorkflowBuilder
from src.bitwarden_workflow_linter.rules.run_actionlint import RunActionlint

yaml = YAML()

@pytest.fixture(name="correct_workflow")
def fixture_correct_workflow():
    workflow = """\
---
name: test
on:
  workflow_dispatch:
  pull_request:

jobs:
  job-key:
    name: Test
    runs-on: ubuntu-latest
    steps:
      - name: Test
        run: echo test

  call-workflow:
    uses: bitwarden/server/.github/workflows/workflow-linter.yml@master

  test-normal-action:
    name: Download Latest
    runs-on: ubuntu-20.04
    steps:
      - name: Checkout
        uses: actions/checkout@2541b1294d2704b0964813337f33b291d3f8596b

      - run: |
          echo test

  test-local-action:
    name: Testing a local action call
    runs-on: ubuntu-20.04
    steps:
      - name: local-action
        uses: ./version-bump
"""
    return WorkflowBuilder.build(workflow=yaml.load(workflow), from_file=False)



@pytest.fixture(name="incorrect_workflow")
def fixture_incorrect_workflow():
    workflow = """\
---
names: test
on:
  workflow_dispatch:
  pull_request:

jobs:
  job-key:
    name: Test
    runs-on: ubuntu-latest
    steps:
      - name: Test
        run: echo test

  call-workflow:
    uses: bitwarden/server/.github/workflows/workflow-linter.yml@master

  test-normal-action:
    name: Download Latest
    runs-on: ubuntu-20.04
    steps:
      - name: Checkout
        uses: actions/checkout@2541b1294d2704b0964813337f33b291d3f8596b

      - run: |
          echo test

  test-local-action:
    name: Testing a local action call
    runs-on: ubuntu-20.04
    steps:
      - name: local-action
        uses: ./version-bump
"""
    return WorkflowBuilder.build(workflow=yaml.load(workflow), from_file=False)

@pytest.fixture(name="rule")
def fixture_rule():
    return RunActionlint()

def test_rule_on_correct_workflow(rule, correct_workflow):
    result, _ = rule.fn(correct_workflow)
    assert result is True

def test_rule_on_correct_workflow(rule, incorrect_workflow):
    result, _ = rule.fn(incorrect_workflow)
    assert result is False
