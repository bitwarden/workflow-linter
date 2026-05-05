"""Test src/bitwarden_workflow_linter/lint.py."""

import argparse

import pytest

from unittest.mock import MagicMock

from src.bitwarden_workflow_linter.lint import LinterCmd
from src.bitwarden_workflow_linter.utils import Settings, LintFinding, LintLevels


@pytest.fixture(name="settings")
def fixture_settings():
    return Settings()


def test_get_max_error_level(settings):
    linter = LinterCmd(settings=settings)

    assert (
        linter.get_max_error_level(
            [
                LintFinding(description="", level=LintLevels.WARNING),
                LintFinding(description="", level=LintLevels.WARNING),
            ]
        )
        == 1
    )

    assert (
        linter.get_max_error_level(
            [
                LintFinding(description="", level=LintLevels.ERROR),
                LintFinding(description="", level=LintLevels.ERROR),
            ]
        )
        == 2
    )

    assert (
        linter.get_max_error_level(
            [
                LintFinding(description="", level=LintLevels.ERROR),
                LintFinding(description="", level=LintLevels.ERROR),
                LintFinding(description="", level=LintLevels.WARNING),
                LintFinding(description="", level=LintLevels.WARNING),
            ]
        )
        == 2
    )


@pytest.fixture(name="linter_with_mock_rules")
def fixture_linter_with_mock_rules(settings):
    linter = LinterCmd(settings=settings)
    linter.rules.workflow = []
    linter.rules.job = []
    linter.rules.step = []
    return linter


def _make_rule(finding):
    rule = MagicMock()
    rule.execute.return_value = finding
    return rule


def test_lint_file_errors_only_suppresses_warnings(linter_with_mock_rules, capsys):
    linter = linter_with_mock_rules
    linter.rules.workflow = [
        _make_rule(LintFinding("warning finding", LintLevels.WARNING)),
        _make_rule(LintFinding("error finding", LintLevels.ERROR)),
    ]

    result = linter.lint_file("tests/fixtures/test.yml", errors_only=True)
    captured = capsys.readouterr()

    assert result == 2
    assert "error finding" in captured.out
    assert "warning finding" not in captured.out


def test_lint_file_errors_only_warnings_only_returns_zero(linter_with_mock_rules, capsys):
    linter = linter_with_mock_rules
    linter.rules.workflow = [
        _make_rule(LintFinding("warning finding", LintLevels.WARNING)),
    ]

    result = linter.lint_file("tests/fixtures/test.yml", errors_only=True)
    captured = capsys.readouterr()

    assert result == 0
    assert "warning finding" not in captured.out


def test_strict_and_errors_only_are_mutually_exclusive():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    LinterCmd.extend_parser(subparsers)

    with pytest.raises(SystemExit):
        parser.parse_args(["lint", "--strict", "--errors-only", "-f", "file.yml"])
