"""Test src/bitwarden_workflow_linter/rules/run_actionlint."""

import os
import pytest
import subprocess
import json

from ruamel.yaml import YAML

from src.bitwarden_workflow_linter.load import WorkflowBuilder
from src.bitwarden_workflow_linter.rules.run_actionlint import (
    RunActionlint,
    install_actionlint_source,
    check_actionlint_local,
    check_actionlint_path,
    install_actionlint,
)
from src.bitwarden_workflow_linter.utils import Settings

yaml = YAML()

def load_config() -> dict:
    """Load configuration from a JSON file."""
    config_path = os.path.join(os.path.dirname(__file__), "../../actionlint_version.json")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with open(config_path, "r") as config_file:
        return json.load(config_file)

@pytest.fixture(name="settings")
def fixture_settings():
    config = load_config()
    return Settings(
        actionlint_version = config["actionlint_version"]
    )

@pytest.fixture(name="rule")
def fixture_rule(settings):
    return RunActionlint(settings=settings)

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

# test_check_actionlint in path
def test_check_actionlint_in_path(monkeypatch, settings):
    def mock_installed(*args, **kwargs):
        return settings.actionlint_version

    monkeypatch.setattr(subprocess, "run", mock_installed)

    result, message = check_actionlint_path("Linux", settings.actionlint_version)
    assert result is True
    assert message == ""

def test_check_actionlint_not_in_path(monkeypatch, settings):
    def mock_run(*args, **kwargs):
        raise subprocess.CalledProcessError(1, args[0])

    monkeypatch.setattr(subprocess, "run", mock_run)

    result, message = check_actionlint_path("Linux", settings.actionlint_version)
    assert result is False
    assert message == "Failed to install Actionlint, please check your package installer or manually install it"

def test_run_actionlint_not_installed(monkeypatch, rule):
    def mock_check_actionlint_path(*args, **kwargs):
        return False, ""

    monkeypatch.setattr(
        "src.bitwarden_workflow_linter.rules.run_actionlint.check_actionlint_path",
        mock_check_actionlint_path,
    )

    workflow = WorkflowBuilder.build("tests/fixtures/test_workflow.yaml")
    result, error = rule.fn(workflow)
    assert result is False
    assert "Actionlint must pass" in error

def test_run_actionlint_installed_error(monkeypatch, rule):
    def mock_check_actionlint_path(*args, **kwargs):
        return True, "/mock/location"

    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 110, stdout="An error occurred")

    monkeypatch.setattr(subprocess, "run", mock_run)
    monkeypatch.setattr(
        "src.bitwarden_workflow_linter.rules.run_actionlint.check_actionlint_path",
        mock_check_actionlint_path,
    )

    workflow = WorkflowBuilder.build("tests/fixtures/test_workflow.yaml")
    result, error = rule.fn(workflow)
    assert result is False
    assert "An error occurred" in error

# test_check_actionlint_installed
def test_check_actionlint_installed_linux(monkeypatch, settings):
    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(subprocess, "run", mock_run)

    result, _ = check_actionlint_path("Linux", settings.actionlint_version)
    assert result is True

def test_check_actionlint_installed_darwin(monkeypatch, settings):
    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(subprocess, "run", mock_run)

    result, _ = check_actionlint_path("Darwin", settings.actionlint_version)
    assert result is True

def test_check_actionlint_installed_windows(monkeypatch, settings):
    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(subprocess, "run", mock_run)

    result, _ = check_actionlint_path("Windows", settings.actionlint_version)
    assert result is True

#test_failed_check_actionlint_installed
def test_failed_check_actionlint_installed_linux(monkeypatch, settings):
    def mock_run(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "cmd")

    monkeypatch.setattr(subprocess, "run", mock_run)

    result, _ = check_actionlint_path("Linux", settings.actionlint_version)
    assert result is False

def test_failed_check_actionlint_installed_darwin(monkeypatch, settings):
    def mock_run(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "cmd")

    monkeypatch.setattr(subprocess, "run", mock_run)

    result, _ = check_actionlint_path("Darwin", settings.actionlint_version)
    assert result is False

def test_failed_check_actionlint_installed_windows(monkeypatch, settings):
    def mock_run(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "cmd")

    monkeypatch.setattr(subprocess, "run", mock_run)

    result, _ = check_actionlint_path("Windows", settings.actionlint_version)
    assert result is False

# test_check_actionlint_installed_locally
def test_check_actionlint_installed_locally_linux(monkeypatch, settings):
    monkeypatch.setattr(os.path, "exists", True)

    result, message = check_actionlint_local("Linux", settings.actionlint_version)

    assert result is True
    assert message == "./actionlint"

def test_check_actionlint_installed_locally_darwin(monkeypatch, settings):
    monkeypatch.setattr(os.path, "exists", True)

    result, message = check_actionlint_local("Darwin", settings.actionlint_version)

    assert result is True
    assert message == "./actionlint"

def test_check_actionlint_installed_locally_windows(monkeypatch, settings):
    def mock_exists(*args, **kwargs):
        return True

    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(os.path, "exists", mock_exists)
    monkeypatch.setattr(subprocess, "run", mock_run)

    result, _ = check_actionlint_local("Windows", settings.actionlint_version)

    assert result is True

# test_install_actionlint
def test_install_actionlint_linux(settings):
    result, _ = install_actionlint("Linux", settings.actionlint_version)
    assert result is True

def test_install_actionlint_darwin(monkeypatch, settings):
    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(subprocess, "run", mock_run)
    result, _ = install_actionlint("Darwin", settings.actionlint_version)
    assert result is True

def test_install_actionlint_windows(monkeypatch, settings):
    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(subprocess, "run", mock_run)
    result, _ = install_actionlint("Windows", settings.actionlint_version)
    assert result is True

def test_install_actionlint_source(monkeypatch, settings):
    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(subprocess, "run", mock_run)

    result, _ = install_actionlint_source("An error occurred", settings.actionlint_version)
    assert result is True

# test non available OS
def test_install_actionlint_non_available_os(settings):
    result, error = install_actionlint("MockOS", settings.actionlint_version)
    assert result is False
    assert "An error occurred when installing Actionlint on MockOS" in error

# test_failed_install_actionlint
def test_failed_install_actionlint_darwin(monkeypatch, settings):
    def mock_run(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "cmd")

    monkeypatch.setattr(subprocess, "run", mock_run)
    result, error = install_actionlint("Darwin", settings.actionlint_version)
    assert result is False
    assert "An error occurred" in error

def test_failed_install_actionlint_windows(monkeypatch, settings):
    def mock_run(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "cmd")

    monkeypatch.setattr(subprocess, "run", mock_run)
    result, error = install_actionlint("Windows", settings.actionlint_version)
    assert result is False
    assert "An error occurred" in error

def test_failed_install_actionlint_linux(monkeypatch, settings):
    def mock_run(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "cmd")

    monkeypatch.setattr(subprocess, "run", mock_run)

    result, error = install_actionlint_source("An error occurred", settings.actionlint_version)
    assert result is False
    assert "An error occurred" in error
