"""Module of a collection of random utilities."""

import importlib.resources
import json
import os

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Self, TypeVar

from ruamel.yaml import YAML

yaml = YAML()


@dataclass
class Colors:
    """Class containing color codes for printing strings to output."""

    black = "30m"
    red = "31m"
    green = "32m"
    yellow = "33m"
    blue = "34m"
    magenta = "35m"
    cyan = "36m"
    white = "37m"


@dataclass
class LintLevel:
    """Class to contain the numeric level and color of linting."""

    code: int
    color: Colors


class LintLevels(LintLevel, Enum):
    """Collection of the different types of LintLevels available."""

    NONE = 0, Colors.white
    WARNING = 1, Colors.yellow
    ERROR = 2, Colors.red


class LintFinding:
    """Represents a problem detected by linting."""

    def __init__(self, description: str, level: LintLevels) -> None:
        self.description = description
        self.level = level

    def __str__(self) -> str:
        """String representation of the class.

        Returns:
        String representation of itself.
        """
        return (
            f"\033[{self.level.color}{self.level.name.lower()}\033[0m "
            f"{self.description}"
        )


@dataclass
class Action:
    """Collection of the metadata associated with a GitHub Action."""

    name: str
    version: str = ""
    sha: str = ""

    def __eq__(self, other: Self) -> bool:
        """Override Action equality.

        Args:
          other:
            Another Action type object to compare

        Return
          The state of equality
        """
        return (
            self.name == other.name
            and self.version == other.version
            and self.sha == other.sha
        )

    def __ne__(self, other: Self) -> bool:
        """Override Action unequality.

        Args:
          other:
            Another Action type object to compare

        Return
          The negation of the state of equality
        """
        return not self.__eq__(other)


class SettingsError(Exception):
    """Custom Exception to indicate an error with loading Settings."""

    pass


SettingsFromFactory = TypeVar("SettingsFromFactory", bound="Settings")

class Settings:
    """Class that contains configuration-as-code for any portion of the app."""

    enabled_rules: list[dict[str, str]]
    approved_actions: dict[str, Action]
    actionlint_version: str
    zizmor_version: str
    zizmor_config_url: Optional[str]
    default_branch: Optional[str]
    blocked_domains: Optional[list[str]]

    def __init__(
        self,
        enabled_rules: Optional[list[dict[str, str]]] = None,
        approved_actions: Optional[dict[str, dict[str, str]]] = None,
        actionlint_version: Optional[str] = None,
        zizmor_version: Optional[str] = None,
        zizmor_config_url: Optional[str] = None,
        default_branch: Optional[str] = None,
        blocked_domains: Optional[list[str]] = None,
    ) -> None:
        """Settings object that can be overridden in settings.py.

        Args:
          enabled_rules:
            All of the python modules that implement a Rule to be run against
            the workflows. These must be available somewhere on the PYTHONPATH
          approved_actions:
            The colleciton of GitHub Actions that are pre-approved to be used
            in any workflow (Required by src.rules.step_approved)
        """
        if enabled_rules is None:
            enabled_rules = []

        if approved_actions is None:
            approved_actions = {}

        if actionlint_version is None:
            actionlint_version = ""

        if zizmor_version is None:
            zizmor_version = ""

        self.actionlint_version = actionlint_version
        self.zizmor_version = zizmor_version
        self.zizmor_config_url = zizmor_config_url
        self.enabled_rules = enabled_rules
        # Handle both dict[str, dict] and dict[str, Action]
        # for approved_actions for testing help
        self.approved_actions = {}
        for name, action in approved_actions.items():
            if isinstance(action, Action):
                # Already an Action object, use it directly
                self.approved_actions[name] = action
            else:
                # Dictionary, create Action object
                self.approved_actions[name] = Action(**action)
        self.default_branch = default_branch
        self.blocked_domains = blocked_domains or []

    @staticmethod
    def factory() -> SettingsFromFactory:
        # load default settings
        with (
            importlib.resources.files("bitwarden_workflow_linter")
            .joinpath("default_settings.yaml")
            .open("r", encoding="utf-8") as file
        ):
            settings = yaml.load(file)

        # load actionlint version
        with (
            importlib.resources.files("bitwarden_workflow_linter")
            .joinpath("actionlint_version.yaml")
            .open("r", encoding="utf-8") as version_file
        ):
            version_data = yaml.load(version_file)
            actionlint_version = version_data["actionlint_version"]

        # load zizmor version
        with (
            importlib.resources.files("bitwarden_workflow_linter")
            .joinpath("zizmor_version.yaml")
            .open("r", encoding="utf-8") as version_file
        ):
            version_data = yaml.load(version_file)
            zizmor_version = version_data["zizmor_version"]

        # load override settings
        settings_filename = "settings.yaml"
        local_settings = None

        if os.path.exists(settings_filename):
            with open(settings_filename, encoding="utf8") as settings_file:
                local_settings = yaml.load(settings_file)

        if local_settings:
            settings.update(local_settings)

        # load approved actions
        if settings["approved_actions_path"] == "default_actions.json":
            with (
                importlib.resources.files("bitwarden_workflow_linter")
                .joinpath("default_actions.json")
                .open("r", encoding="utf-8") as file
            ):
                settings["approved_actions"] = json.load(file)
        else:
            with open(
                settings["approved_actions_path"], "r", encoding="utf8"
            ) as action_file:
                settings["approved_actions"] = json.load(action_file)

        default_branch = settings.get("default_branch")
        if default_branch is None or len(default_branch) == 0:
            raise Exception("The default_branch is not set in the default_settings.yaml file")

        return Settings(
            enabled_rules=settings["enabled_rules"],
            approved_actions=settings["approved_actions"],
            actionlint_version=actionlint_version,
            zizmor_version=zizmor_version,
            zizmor_config_url=settings.get("zizmor_config_url"),
            default_branch=default_branch,
            blocked_domains=settings.get("blocked_domains", []),
        )
