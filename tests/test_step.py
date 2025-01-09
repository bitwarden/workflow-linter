"""Test src/bitwarden_workflow_linter/models/step.py."""

import json
import pytest

from ruamel.yaml import YAML

from src.bitwarden_workflow_linter.models.step import Step


@pytest.fixture(name="default_step")
def fixture_default_step():
    step_str = """\
name: Default Step
run: echo "test"
"""
    yaml = YAML()
    step_yaml = yaml.load(step_str)
    return Step.init(0, "default", step_yaml)


@pytest.fixture(name="uses_step")
def fixture_uses_step():
    step_str = """\
name: Download Artifacts
uses: bitwarden/download-artifacts@main # v1.0.0
with:
    workflow: upload-test-artifacts.yml
    artifacts: artifact
    path: artifact
    branch: main

"""
    yaml = YAML()
    step_yaml = yaml.load(step_str)
    return Step.init(0, "default", step_yaml)


@pytest.fixture(name="uses_step_no_comments")
def fixture_uses_step_no_comments():
    step_str = """\
name: Download Artifacts
uses: bitwarden/download-artifacts@main
with:
    workflow: upload-test-artifacts.yml
    artifacts: artifact
    path: artifact
    branch: main

"""
    yaml = YAML()
    step_yaml = yaml.load(step_str)
    return Step.init(0, "default", step_yaml)


@pytest.fixture(name="uses_step_no_ref")
def fixture_uses_step_no_ref():
    step_str = """\
name: Run Local Workflow
uses: ./.github/workflows/_local.yml
"""
    yaml = YAML()
    step_yaml = yaml.load(step_str)
    return Step.init(0, "default", step_yaml)


@pytest.fixture(name="uses_step_no_ref_with_comments")
def fixture_uses_step_no_ref_with_comments():
    step_str = """\
name: Run Local Workflow
uses: ./.github/workflows/_local.yml # A comment
"""
    yaml = YAML()
    step_yaml = yaml.load(step_str)
    return Step.init(0, "default", step_yaml)


def test_step_default(default_step):
    assert default_step.key == 0
    assert default_step.job == "default"
    assert default_step.name == "Default Step"
    assert default_step.env is None
    assert default_step.uses is None
    assert default_step.uses_with is None
    assert default_step.run == 'echo "test"'


def test_step_no_keyword_field(default_step):
    assert default_step.uses_with is None
    assert "uses_with" not in default_step.to_json()


def test_step_extra_kwargs(default_step):
    with pytest.raises(Exception):
        assert default_step.extra == "test"


def test_step_keyword_field(uses_step):
    expected_response = {
        "workflow": "upload-test-artifacts.yml",
        "artifacts": "artifact",
        "path": "artifact",
        "branch": "main",
    }

    step_json = uses_step.to_json()
    assert uses_step.key == 0
    assert "uses_with" not in step_json
    assert "with" in step_json
    assert json.loads(uses_step.to_json())["with"] == expected_response


def test_step_comment(uses_step):
    assert uses_step.key == 0
    assert uses_step.job == "default"
    assert uses_step.uses_ref == "main"
    assert uses_step.uses_version == "v1.0.0"
    assert uses_step.uses_comment == "# v1.0.0"


def test_step_no_comments(uses_step_no_comments):
    assert uses_step_no_comments.key == 0
    assert uses_step_no_comments.job == "default"
    assert uses_step_no_comments.uses_ref == "main"
    assert uses_step_no_comments.uses_version is None
    assert uses_step_no_comments.uses_comment is None


def test_step_no_ref(uses_step_no_ref):
    assert uses_step_no_ref.key == 0
    assert uses_step_no_ref.job == "default"
    assert uses_step_no_ref.uses_ref is None
    assert uses_step_no_ref.uses_version is None
    assert uses_step_no_ref.uses_comment is None


def test_step_no_ref_with_comments(uses_step_no_ref_with_comments):
    assert uses_step_no_ref_with_comments.key == 0
    assert uses_step_no_ref_with_comments.job == "default"
    assert uses_step_no_ref_with_comments.uses_ref is None
    assert (
        uses_step_no_ref_with_comments.uses_version == "comment"
    )  # We are not currently validating the version matches a specific format
    assert uses_step_no_ref_with_comments.uses_comment == "# A comment"
