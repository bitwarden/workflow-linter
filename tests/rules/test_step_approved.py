"""Test src/bitwarden_workflow_linter/rules/step_approved.py."""

import pytest

from ruamel.yaml import YAML

from src.bitwarden_workflow_linter.load import WorkflowBuilder
from src.bitwarden_workflow_linter.rules.step_approved import RuleStepUsesApproved
from src.bitwarden_workflow_linter.utils import Settings


yaml = YAML()


@pytest.fixture(name="settings")
def fixture_settings():
    return Settings(
        approved_actions={
            "actions/checkout": {
                "name": "actions/checkout",
                "version": "v4.1.1",
                "sha": "b4ffde65f46336ab88eb53be808477a3936bae11",
            },
            "actions/download-artifact": {
                "name": "actions/download-artifact",
                "version": "v4.1.0",
                "sha": "f44cd7b40bfd40b6aa1cc1b9b5b7bf03d3c67110",
            },
        }
    )


@pytest.fixture(name="correct_workflow")
def fixture_correct_workflow():
    workflow = """\
---
on:
  workflow_dispatch:

jobs:
  job-key:
    runs-on: ubuntu-22.04
    steps:
      - name: Checkout Branch
        uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1

      - name: Test Bitwarden Action
        uses: bitwarden/gh-actions/get-keyvault-secrets@main

      - name: Test Local Action
        uses: ./actions/test-action

      - name: Test Run Action
        run: echo "test"
"""
    return WorkflowBuilder.build(workflow=yaml.load(workflow), from_file=False)


@pytest.fixture(name="incorrect_workflow")
def fixture_incorrect_workflow():
    workflow = """\
---
on:
  workflow_dispatch:

jobs:
  job-key:
    runs-on: ubuntu-22.04
    steps:
      - name: Checkout Branch
        uses: joseph-flinn/action-DNE@main

      - name: Checkout Branch with Ref
        uses: notbitwarden/subfolder/action-DNE@main
        with:
            ref: main

"""
    return WorkflowBuilder.build(workflow=yaml.load(workflow), from_file=False)


@pytest.fixture(name="rule")
def fixture_rule(settings):
    return RuleStepUsesApproved(settings=settings)


def test_rule_on_correct_workflow(rule, correct_workflow):
    result, _ = rule.fn(correct_workflow.jobs["job-key"].steps[0])
    assert result is True

    result, _ = rule.fn(correct_workflow.jobs["job-key"].steps[1])
    assert result is True

    result, _ = rule.fn(correct_workflow.jobs["job-key"].steps[2])
    assert result is True

    result, _ = rule.fn(correct_workflow.jobs["job-key"].steps[3])
    assert result is True


def test_rule_on_incorrect_workflow(rule, incorrect_workflow):
    result, message = rule.fn(incorrect_workflow.jobs["job-key"].steps[0])
    assert result is False
    assert "New Action detected" in message

    result, message = rule.fn(incorrect_workflow.jobs["job-key"].steps[1])
    assert result is False
    assert "New Action detected" in message


def test_fail_compatibility(rule, correct_workflow):
    finding = rule.execute(correct_workflow)
    assert "Workflow not compatible with" in finding.description

    finding = rule.execute(correct_workflow.jobs["job-key"])
    assert "Job not compatible with" in finding.description


def test_multi_segment_action_approved():
    """Test multi-segment actions pass validation when approved."""
    # Create settings with a multi-segment action in the approved list
    settings = Settings(
        approved_actions={
            "oxsecurity/megalinter/flavors/dotnetweb": {
                "name": "oxsecurity/megalinter/flavors/dotnetweb",
                "version": "v9.2.0",
                "sha": "55a59b24a441e0e1943080d4a512d827710d4a9d",
            },
            "aws-actions/amazon-ecr-login/outputs": {
                "name": "aws-actions/amazon-ecr-login/outputs",
                "version": "v2.0.1",
                "sha": "abc123def456",
            },
        }
    )

    # Create a workflow that uses the multi-segment action
    workflow = """\
---
on:
  workflow_dispatch:

jobs:
  job-key:
    runs-on: ubuntu-22.04
    steps:
      - name: Use MegaLinter flavor
        uses: oxsecurity/megalinter/flavors/dotnetweb@55a59b24a441e0e1943080d4a512d827710d4a9d # v9.2.0

      - name: Use AWS ECR Login with subdirectory
        uses: aws-actions/amazon-ecr-login/outputs@abc123def456 # v2.0.1
"""
    workflow_obj = WorkflowBuilder.build(workflow=yaml.load(workflow), from_file=False)

    # Create rule with the settings
    rule = RuleStepUsesApproved(settings=settings)

    # Test first step (oxsecurity multi-segment action)
    result, message = rule.fn(workflow_obj.jobs["job-key"].steps[0])
    assert result is True, f"Multi-segment action should be approved but got: {message}"

    # Test second step (aws-actions multi-segment action)
    result, message = rule.fn(workflow_obj.jobs["job-key"].steps[1])
    assert result is True, f"Multi-segment action should be approved but got: {message}"


def test_multi_segment_action_not_approved():
    """Test that multi-segment actions correctly fail when not in approved list."""
    # Create settings WITHOUT the multi-segment action
    settings = Settings(
        approved_actions={
            "actions/checkout": {
                "name": "actions/checkout",
                "version": "v4.1.1",
                "sha": "b4ffde65f46336ab88eb53be808477a3936bae11",
            },
        }
    )

    # Create a workflow that uses an unapproved multi-segment action
    workflow = """\
---
on:
  workflow_dispatch:

jobs:
  job-key:
    runs-on: ubuntu-22.04
    steps:
      - name: Use unapproved MegaLinter flavor
        uses: oxsecurity/megalinter/flavors/javascript@somesha123 # v9.0.0
"""
    workflow_obj = WorkflowBuilder.build(workflow=yaml.load(workflow), from_file=False)

    # Create rule with the settings
    rule = RuleStepUsesApproved(settings=settings)

    # Test that it fails validation
    result, message = rule.fn(workflow_obj.jobs["job-key"].steps[0])
    assert result is False, "Unapproved multi-segment action should fail validation"
    assert "New Action detected" in message
    assert "oxsecurity/megalinter/flavors/javascript" in message
