"""Test src/bitwarden_workflow_linter/rules/underscore_outputs.py."""

import pytest

from ruamel.yaml import YAML

from src.bitwarden_workflow_linter.load import WorkflowBuilder
from src.bitwarden_workflow_linter.rules.underscore_outputs import RuleUnderscoreOutputs

yaml = YAML()


@pytest.fixture(name="correct_workflow")
def fixture_correct_workflow():
    workflow = """\
---
name: Test Correct Workflow
on:
  workflow_dispatch:
    outputs:
      registry:
        value: 'Test Value'
      some_registry:
        value: 'Test Value'
  workflow_call:
    outputs:
      registry:
        value: 'Test Value'
      some_registry:
        value: 'Test Value'
  push: {}

jobs:
  job-key:
    name: Test Correct Job
    runs-on: ubuntu-22.04
    outputs:
      test_key_job: ${{ steps.test_output_1.outputs.test_key }}
    steps:
      - name: Test output in one-line run step
        id: test_output_1
        run: echo "test_key_1=Test-Value1" >> $GITHUB_OUTPUT

      - name: Test output in multi-line run step
        id: test_output_2
        run: |
          echo
          fake-command=Test-Value2
          echo "test_key_2=$REF" >> $GITHUB_OUTPUT
          echo "deployed_ref=$DEPLOYED_REF" >> $GITHUB_OUTPUT

      - name: Test step with one-line run and no Output
        id: test_output_3
        run: echo "test_key_3"

      - name: Test step with multi-line run and no Output
        id: test_output_4
        run: |
          echo
          fake-command=Test-Value4
          echo "test_key_4"
          echo "deployed_ref"

      - name: Test step with no run
        id: test_output_5
        uses: actions/checkout@v2
        with:
          ref: ${{ github.ref }}
          fetch-depth: 0
"""
    return WorkflowBuilder.build(workflow=yaml.load(workflow), from_file=False)


@pytest.fixture(name="incorrect_workflow")
def fixture_incorrect_workflow():
    workflow = """\
---
name: Test Incorrect Workflow
on:
  workflow_dispatch:
    outputs:
      registry-1:
        value: 'Test Value'
      some_registry-1:
        value: 'Test Value'
  workflow_call:
    outputs:
      registry-2:
        value: 'Test Value'
  push: {}

jobs:
  job-key:
    name: Test Incorrect Job
    runs-on: ubuntu-22.04
    outputs:
      test-key-1: ${{ steps.test_output_1.outputs.test_key }}
    steps:
      - name: Test step with one-line run and no Output
        id: test_output_3
        run: echo "test-key-3"

      - name: Test step with multi-line run and no Output
        id: test_output_4
        run: |
          echo
          fake-command=Test-Value4
          echo "test-key-4"
          echo "deployed-ref"
"""
    return WorkflowBuilder.build(workflow=yaml.load(workflow), from_file=False)


@pytest.fixture(name="push_only_workflow")
def fixture_push_only_workflow():
    workflow = """\
---
name: Push Only
on:
  push: {}

jobs:
  job-key:
    name: Test
    runs-on: ubuntu-latest
    steps:
      - run: echo test

"""
    return WorkflowBuilder.build(workflow=yaml.load(workflow), from_file=False)


@pytest.fixture(name="misc_workflow")
def fixture_misc_workflow():
    workflow = """\
---
name: Misc Workflow
on:
  push: {}

jobs:
  job-key:
    runs-on: ubuntu-22.04
    steps:
      - name: Test Step
        run: |
          echo "test_value=$does_it_break" >> /tmp/test

      - name: Test Step 2
        run: |
          TEST_FILE=/tmp/test2
          echo "test_value=$does_it_break" >> $TEST_FILE
"""
    return WorkflowBuilder.build(workflow=yaml.load(workflow), from_file=False)


@pytest.fixture(name="no_output_workflow")
def fixture_no_output_workflow():
    workflow = """\
---
name: No Output Workflow
on:
  workflow_dispatch:
    inputs: {}
  workflow_call: {}

jobs:
  job-key:
    name: Test
    runs-on: ubuntu-latest
    steps:
      - run: echo test
"""
    return WorkflowBuilder.build(workflow=yaml.load(workflow), from_file=False)


@pytest.fixture(name="rule")
def fixture_rule():
    return RuleUnderscoreOutputs()


def test_rule_on_correct_workflow(rule, correct_workflow):
    result, _ = rule.fn(correct_workflow)
    assert result is True


def test_rule_on_incorrect_workflow(rule, incorrect_workflow):
    result, _ = rule.fn(incorrect_workflow)
    assert result is False


def test_rule_on_correct_job(rule, correct_workflow):
    result, _ = rule.fn(correct_workflow.jobs["job-key"])
    assert result is True


def test_rule_on_incorrect_job(rule, incorrect_workflow):
    result, _ = rule.fn(incorrect_workflow.jobs["job-key"])
    assert result is False


def test_rule_on_correct_step(rule, correct_workflow):
    result, _ = rule.fn(correct_workflow.jobs["job-key"].steps[0])
    assert result is True

    result, _ = rule.fn(correct_workflow.jobs["job-key"].steps[1])
    assert result is True

    result, _ = rule.fn(correct_workflow.jobs["job-key"].steps[2])
    assert result is True

    result, _ = rule.fn(correct_workflow.jobs["job-key"].steps[3])
    assert result is True

    result, _ = rule.fn(correct_workflow.jobs["job-key"].steps[4])
    assert result is True


def test_rule_on_incorrect_step(rule, incorrect_workflow):
    result, _ = rule.fn(incorrect_workflow.jobs["job-key"].steps[0])
    assert result is True

    result, _ = rule.fn(incorrect_workflow.jobs["job-key"].steps[1])
    assert result is True


def test_rule_on_push_only_workflow(rule, push_only_workflow):
    result, _ = rule.fn(push_only_workflow)
    assert result is True


def test_rule_on_misc_workflow(rule, misc_workflow):
    result, _ = rule.fn(misc_workflow.jobs["job-key"].steps[0])
    assert result is True

    result, _ = rule.fn(misc_workflow.jobs["job-key"].steps[1])
    assert result is True


def test_rule_on_no_output_workflow(rule, no_output_workflow):
    result, _ = rule.fn(no_output_workflow)
    assert result is True
