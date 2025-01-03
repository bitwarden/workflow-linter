"""Test src/bitwarden_workflow_linter/rules/run_actionlint."""

import pytest

from ruamel.yaml import YAML

from src.bitwarden_workflow_linter.load import WorkflowBuilder
from src.bitwarden_workflow_linter.rules.run_actionlint import RunActionlint

yaml = YAML()

@pytest.fixture(name="rule")
def fixture_rule():
    return RunActionlint()

def test_rule_on_correct_workflow(rule):
    correct_workflow =  WorkflowBuilder.build("tests/fixtures/test_workflow.yaml")
    result, _ = rule.fn(correct_workflow)
    assert result is False


def test_rule_on_incorrect_workflow(rule):
    incorrect_workflow = WorkflowBuilder.build("tests/fixtures/test_workflow_incorrect.yaml")
    result, _ = rule.fn(incorrect_workflow)
    assert result is False