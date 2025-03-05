"""Test src/bitwarden_workflow_linter/rules/permissions_exist.py."""

import pytest

from ruamel.yaml import YAML

from src.bitwarden_workflow_linter.load import WorkflowBuilder
from src.bitwarden_workflow_linter.rules.permissions_exist import RulePermissionsExist


yaml = YAML()


@pytest.fixture(name="correct_workflow_read_all")
def fixture_correct_workflow_read_all():
    workflow = """\
---
name: Test Workflow

on:
  workflow_dispatch:

permissions: read-all

jobs:
  job-key:
    name: Test
    runs-on: ubuntu-latest
    steps:
      - name: Test
        run: echo test
"""
    return WorkflowBuilder.build(workflow=yaml.load(workflow), from_file=False)


@pytest.fixture(name="correct_workflow_scoped_permissions")
def fixture_correct_workflow_scoped_permissions():
    workflow = """\
---
on:
  workflow_dispatch:

permissions:
  checks: write
  contents: read
  id-token: write
  pull-requests: write


jobs:
  job-key:
    runs-on: ubuntu-latest
    steps:
      - run: echo test
"""
    return WorkflowBuilder.build(workflow=yaml.load(workflow), from_file=False)


@pytest.fixture(name="incorrect_workflow_missing_permissions")
def fixture_incorrect_workflow_missing_permissions():
    workflow = """\
---
on:
  workflow_dispatch:

jobs:
  job-key:
    runs-on: ubuntu-latest
    steps:
      - run: echo test
"""
    return WorkflowBuilder.build(workflow=yaml.load(workflow), from_file=False)


@pytest.fixture(name="rule")
def fixture_rule():
    return RulePermissionsExist()


def test_rule_on_correct_workflow_read_all(rule, correct_workflow_read_all):
    result, _ = rule.fn(correct_workflow_read_all)
    assert result is True


def test_rule_on_correct_workflow_scoped_permissions(
    rule, correct_workflow_scoped_permissions
):
    result, _ = rule.fn(correct_workflow_scoped_permissions)
    assert result is True


def test_rule_on_incorrect_workflow_missing_permissions(
    rule, incorrect_workflow_missing_permissions
):
    result, _ = rule.fn(incorrect_workflow_missing_permissions)
    assert result is False
