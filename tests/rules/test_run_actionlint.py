"""Test src/bitwarden_workflow_linter/rules/name_exists.py."""

import pytest

from ruamel.yaml import YAML

from src.bitwarden_workflow_linter.load import WorkflowBuilder
from src.bitwarden_workflow_linter.rules.run_actionlint import RunActionlint


yaml = YAML()

def test_rule_on_correct_workflow(rule, correct_workflow):
    result, _ = rule.fn(correct_workflow)
    assert result is True


def test_rule_on_incorrect_workflow(rule, incorrect_workflow):
    print(f"Workflow name: {incorrect_workflow.name}")
    result, _ = rule.fn(incorrect_workflow)
    assert result is False
