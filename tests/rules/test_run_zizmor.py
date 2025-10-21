"""Test src/bitwarden_workflow_linter/rules/run_zizmor."""

import pytest
import subprocess
import tempfile
import urllib.request
import os

import src.bitwarden_workflow_linter.rules.run_zizmor as zizmor_module
from src.bitwarden_workflow_linter.utils import Settings
from src.bitwarden_workflow_linter.load import WorkflowBuilder
from src.bitwarden_workflow_linter.rules.run_zizmor import (
    RunZizmor,
    install_zizmor,
    check_zizmor_path,
    download_config_file,
)

settings = Settings.factory()


@pytest.fixture(name="rule")
def fixture_rule():
    return RunZizmor(settings)


def test_rule_on_correct_workflow(rule):
    """Test zizmor rule on a correct workflow."""
    rule.settings = settings
    correct_workflow = WorkflowBuilder.build("tests/fixtures/test_workflow.yaml")

    # Mock successful zizmor execution
    def mock_check_zizmor_path(*args, **kwargs):
        return True, ""

    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 0, stdout="")

    original_check = zizmor_module.check_zizmor_path
    original_run = subprocess.run

    try:
        zizmor_module.check_zizmor_path = mock_check_zizmor_path
        subprocess.run = mock_run

        result, _ = rule.fn(correct_workflow)
        assert result is True
    finally:
        zizmor_module.check_zizmor_path = original_check
        subprocess.run = original_run


def test_rule_on_workflow_with_findings(rule):
    """Test zizmor rule on a workflow that has findings."""
    rule.settings = settings
    workflow = WorkflowBuilder.build("tests/fixtures/test_workflow.yaml")

    # Mock zizmor execution with findings
    def mock_check_zizmor_path(*args, **kwargs):
        return True, ""

    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 1,
                                           stdout="warning: insecure action found")

    original_check = zizmor_module.check_zizmor_path
    original_run = subprocess.run

    try:
        zizmor_module.check_zizmor_path = mock_check_zizmor_path
        subprocess.run = mock_run

        result, error = rule.fn(workflow)
        assert result is False
        assert "warning: insecure action found" in error
    finally:
        zizmor_module.check_zizmor_path = original_check
        subprocess.run = original_run


def test_install_zizmor(monkeypatch):
    """Test installing zizmor."""
    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(subprocess, "run", mock_run)
    result, _ = install_zizmor("Error", settings.zizmor_version)
    assert result is True


def test_failed_install_zizmor(monkeypatch):
    """Test failed zizmor installation."""
    def mock_run(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "cmd")

    monkeypatch.setattr(subprocess, "run", mock_run)
    result, error = install_zizmor("Error", settings.zizmor_version)
    assert result is False
    assert "check pip installation" in error


def test_install_zizmor_linux(monkeypatch):
    """Test zizmor installation on Linux."""
    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(subprocess, "run", mock_run)
    result, _ = install_zizmor("Linux", settings.zizmor_version)
    assert result is True


def test_install_zizmor_darwin(monkeypatch):
    """Test zizmor installation on Darwin/macOS."""
    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(subprocess, "run", mock_run)
    result, _ = install_zizmor("Darwin", settings.zizmor_version)
    assert result is True


def test_install_zizmor_windows(monkeypatch):
    """Test zizmor installation on Windows."""
    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(subprocess, "run", mock_run)
    result, _ = install_zizmor("Windows", settings.zizmor_version)
    assert result is True


def test_check_zizmor_path_installed(monkeypatch):
    """Test checking zizmor when it's already installed."""
    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args, 0, stdout=f"zizmor {settings.zizmor_version}"
        )

    monkeypatch.setattr(subprocess, "run", mock_run)
    result, _ = check_zizmor_path("Linux", settings.zizmor_version)
    assert result is True


def test_check_zizmor_path_not_installed(monkeypatch):
    """Test checking zizmor when it's not installed."""
    def mock_run(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(subprocess, "run", mock_run)
    result, _ = check_zizmor_path("Linux", settings.zizmor_version)
    assert result is False


def test_check_zizmor_path_wrong_version(monkeypatch):
    """Test checking zizmor when wrong version is installed."""
    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 0, stdout="zizmor 0.1.0")

    def mock_install(*args, **kwargs):
        return True, ""

    monkeypatch.setattr(subprocess, "run", mock_run)
    monkeypatch.setattr(
        "src.bitwarden_workflow_linter.rules.run_zizmor.install_zizmor",
        mock_install
    )
    result, _ = check_zizmor_path("Linux", settings.zizmor_version)
    assert result is True


def test_download_config_file_success(monkeypatch):
    """Test downloading config file successfully."""
    mock_config = "# zizmor config\nrules = []"

    class MockResponse:
        def read(self):
            return mock_config.encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    def mock_urlopen(url):
        return MockResponse()

    original_urlopen = urllib.request.urlopen

    try:
        urllib.request.urlopen = mock_urlopen
        config_path = download_config_file("https://example.com/config.yaml")

        assert config_path is not None

        # Verify the file was created with correct content
        with open(config_path, "r") as f:
            content = f.read()
            assert mock_config in content

        # Clean up
        os.unlink(config_path)
    finally:
        urllib.request.urlopen = original_urlopen

def test_download_config_file_failure():
    """Test downloading config file failure."""
    config_path = download_config_file("https://invalid-url")
    assert config_path is None


def test_download_config_file_empty_url():
    """Test downloading config file with empty URL."""
    config_path = download_config_file("")
    assert config_path is None


def test_rule_with_config_url(rule):
    """Test zizmor rule with config URL."""
    # Create a temporary settings object with config URL
    temp_settings = Settings(
        enabled_rules=settings.enabled_rules,
        approved_actions=settings.approved_actions,
        actionlint_version=settings.actionlint_version,
        zizmor_version=settings.zizmor_version,
        zizmor_config_url="https://example.com/zizmor.yml",
        default_branch=settings.default_branch,
        blocked_domains=settings.blocked_domains
    )
    rule.settings = temp_settings

    workflow = WorkflowBuilder.build("tests/fixtures/test_workflow.yaml")

    # Mock successful operations
    def mock_check_zizmor_path(*args, **kwargs):
        return True, ""

    def mock_download_config_file(url):
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False)
        temp_file.write("# mock config")
        temp_file.close()
        return temp_file.name

    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 0, stdout="")

    original_check = zizmor_module.check_zizmor_path
    original_download = zizmor_module.download_config_file
    original_run = subprocess.run

    try:
        zizmor_module.check_zizmor_path = mock_check_zizmor_path
        zizmor_module.download_config_file = mock_download_config_file
        subprocess.run = mock_run

        result, _ = rule.fn(workflow)
        assert result is True
    finally:
        zizmor_module.check_zizmor_path = original_check
        zizmor_module.download_config_file = original_download
        subprocess.run = original_run


def test_rule_without_filename(rule):
    """Test zizmor rule with workflow without filename."""
    rule.settings = settings
    workflow = WorkflowBuilder.build("tests/fixtures/test_workflow.yaml")
    workflow.filename = None

    with pytest.raises(AttributeError, match="Running zizmor without a filename"):
        rule.fn(workflow)


def test_rule_without_zizmor_version():
    """Test zizmor rule without zizmor version in settings."""
    temp_settings = Settings(
        enabled_rules=settings.enabled_rules,
        approved_actions=settings.approved_actions,
        actionlint_version=settings.actionlint_version,
        zizmor_version="",  # Empty version
        default_branch=settings.default_branch,
        blocked_domains=settings.blocked_domains
    )
    rule = RunZizmor(temp_settings)
    workflow = WorkflowBuilder.build("tests/fixtures/test_workflow.yaml")

    with pytest.raises(KeyError, match="zizmor_version"):
        rule.fn(workflow)


def test_rule_zizmor_not_installed(rule):
    """Test zizmor rule when zizmor is not installed."""
    rule.settings = settings
    workflow = WorkflowBuilder.build("tests/fixtures/test_workflow.yaml")

    def mock_check_zizmor_path(*args, **kwargs):
        return False, "zizmor not found"

    original_check = zizmor_module.check_zizmor_path

    try:
        zizmor_module.check_zizmor_path = mock_check_zizmor_path

        result, error = rule.fn(workflow)
        assert result is False
        assert "zizmor not found" in error
    finally:
        zizmor_module.check_zizmor_path = original_check
