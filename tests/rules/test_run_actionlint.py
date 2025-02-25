"""Test src/bitwarden_workflow_linter/rules/run_actionlint."""

import os
import pytest
import subprocess

from ruamel.yaml import YAML

from src.bitwarden_workflow_linter.load import WorkflowBuilder
from src.bitwarden_workflow_linter.rules.run_actionlint import (
    RunActionlint,
    install_actionlint_source,
    check_actionlint,
    install_actionlint,
)

yaml = YAML()

@pytest.fixture(name="rule")
def fixture_rule():
    return RunActionlint()

def test_rule_on_correct_workflow(rule):
    correct_workflow = WorkflowBuilder.build("tests/fixtures/test_workflow.yaml")
    result, _ = rule.fn(correct_workflow)
    assert result is True

def test_rule_on_incorrect_workflow(rule):
    incorrect_workflow = WorkflowBuilder.build(
        "tests/fixtures/test_workflow_incorrect.yaml"
    )
    result, _ = rule.fn(incorrect_workflow)
    assert result is False

def test_check_actionlint_not_in_path(monkeypatch):
    def mock_run(*args, **kwargs):
        raise subprocess.CalledProcessError(1, args[0])

    monkeypatch.setattr(subprocess, "run", mock_run)

    result, message = check_actionlint("linux")
    assert result is False
    assert message == "Failed to install Actionlint, please check your package installer or manually install it"

# test_run_actionlint
def test_run_actionlint_installed(monkeypatch, rule):
    def mock_check_actionlint(*args, **kwargs):
        return True, "/mock/location"

    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 0, stdout="")

    monkeypatch.setattr(subprocess, "run", mock_run)
    monkeypatch.setattr(
        "src.bitwarden_workflow_linter.rules.run_actionlint.check_actionlint",
        mock_check_actionlint,
    )

    workflow = WorkflowBuilder.build("tests/fixtures/test_workflow.yaml")
    result, _ = rule.fn(workflow)
    assert result is True

def test_run_actionlint_not_installed(monkeypatch, rule):
    def mock_check_actionlint(*args, **kwargs):
        return False, ""

    monkeypatch.setattr(
        "src.bitwarden_workflow_linter.rules.run_actionlint.check_actionlint",
        mock_check_actionlint,
    )

    workflow = WorkflowBuilder.build("tests/fixtures/test_workflow.yaml")
    result, error = rule.fn(workflow)
    assert result is False
    assert "Actionlint must pass" in error

def test_run_actionlint_installed_error(monkeypatch, rule):
    def mock_check_actionlint(*args, **kwargs):
        return True, "/mock/location"

    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 110, stdout="An error occurred")

    monkeypatch.setattr(subprocess, "run", mock_run)
    monkeypatch.setattr(
        "src.bitwarden_workflow_linter.rules.run_actionlint.check_actionlint",
        mock_check_actionlint,
    )

    workflow = WorkflowBuilder.build("tests/fixtures/test_workflow.yaml")
    result, error = rule.fn(workflow)
    assert result is False
    assert "An error occurred" in error

# test_check_actionlint_installed
def test_check_actionlint_installed_linux(monkeypatch):
    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(subprocess, "run", mock_run)

    result, _ = check_actionlint("Linux")
    assert result is True

def test_check_actionlint_installed_darwin(monkeypatch):
    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(subprocess, "run", mock_run)

    result, _ = check_actionlint("Darwin")
    assert result is True

def test_check_actionlint_installed_windows(monkeypatch):
    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(subprocess, "run", mock_run)

    result, _ = check_actionlint("Windows")
    assert result is True

#test_failed_check_actionlint_installed
def test_failed_check_actionlint_installed_linux(monkeypatch):
    def mock_run(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "cmd")

    monkeypatch.setattr(subprocess, "run", mock_run)

    result, _ = check_actionlint("Linux")
    assert result is False

def test_failed_check_actionlint_installed_darwin(monkeypatch):
    def mock_run(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "cmd")

    monkeypatch.setattr(subprocess, "run", mock_run)

    result, _ = check_actionlint("Darwin")
    assert result is False

def test_failed_check_actionlint_installed_windows(monkeypatch):
    def mock_run(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "cmd")

    monkeypatch.setattr(subprocess, "run", mock_run)

    result, _ = check_actionlint("Windows")
    assert result is False

# test_check_actionlint_installed_locally
def test_check_actionlint_installed_locally_linux(monkeypatch):
    monkeypatch.setattr(os.path, "exists", True)
    
    result, message = check_actionlint("Linux")

    assert result is True
    assert message == ""

def test_check_actionlint_installed_locally_darwin(monkeypatch):
    monkeypatch.setattr(os.path, "exists", True)
    
    result, message = check_actionlint("Darwin")

    assert result is True
    assert message == ""

def test_check_actionlint_installed_locally_windows(monkeypatch):
    monkeypatch.setattr(os.path, "exists", True)
    
    result, message = check_actionlint("Windows")

    assert result is True
    assert message == ""

# test_install_actionlint
def test_install_actionlint_linux():
    result, _ = install_actionlint("Linux")
    assert result is True

def test_install_actionlint_darwin(monkeypatch):
    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(subprocess, "run", mock_run)
    result, _ = install_actionlint("Darwin")
    assert result is True

def test_install_actionlint_windows(monkeypatch):
    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(subprocess, "run", mock_run)
    result, _ = install_actionlint("Windows")
    assert result is True

def test_install_actionlint_source(monkeypatch):
    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(subprocess, "run", mock_run)

    result, _ = install_actionlint_source("An error occurred")
    assert result is True

# test_failed_install_actionlint
def test_failed_install_actionlint_darwin(monkeypatch):
    def mock_run(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "cmd")

    monkeypatch.setattr(subprocess, "run", mock_run)
    result, error = install_actionlint("Darwin")
    assert result is False
    assert "An error occurred" in error

def test_failed_install_actionlint_windows(monkeypatch):
    def mock_run(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "cmd")

    monkeypatch.setattr(subprocess, "run", mock_run)
    result, error = install_actionlint("Windows")
    assert result is False
    assert "An error occurred" in error

def test_failed_install_actionlint_linux(monkeypatch):
    def mock_run(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "cmd")

    monkeypatch.setattr(subprocess, "run", mock_run)

    result, error = install_actionlint_source("An error occurred")
    assert result is False
    assert "An error occurred" in error
