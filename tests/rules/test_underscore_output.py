"""Test src/bitwarden_workflow_linter/rules/underscore_outputs.py."""

import pytest

from ruamel.yaml import YAML

from src.bitwarden_workflow_linter.load import WorkflowBuilder
from src.bitwarden_workflow_linter.rules.underscore_outputs import RuleUnderscoreOutputs

yaml = YAML()


@pytest.fixture(name="correct_workflow")
def fixture_correct_workflow():
    workflow = """\
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
jobs:
  job-key:
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

      - name: Test step with no run
        id: test_output_3
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
on:
  workflow_dispatch:
    outputs:
      registry-1:
        value: 'Test Value'
  workflow_call:
    outputs:
      registry-2:
        value: 'Test Value'
jobs:
  job-key:
    runs-on: ubuntu-22.04
    outputs:
      test-key-1: ${{ steps.test_output_1.outputs.test_key }}
    steps:
      - name: Test output in one-line run step
        id: test_output_1
        run: echo "test-key-1=Test-Value1" >> $GITHUB_OUTPUT

      - name: Test output in multi-line run step
        id: test_output_2
        run: |
          echo
          fake-command
          echo "test-key-2=$REF" >> $GITHUB_OUTPUT
          echo "deployed-ref=$DEPLOYED_REF" >> $GITHUB_OUTPUT
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


def test_rule_on_incorrect_step(rule, incorrect_workflow):
    result, _ = rule.fn(incorrect_workflow.jobs["job-key"].steps[0])
    assert result is False

    result, _ = rule.fn(incorrect_workflow.jobs["job-key"].steps[1])
    assert result is False
