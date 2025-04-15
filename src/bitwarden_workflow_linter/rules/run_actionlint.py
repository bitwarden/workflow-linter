"""A Rule to run actionlint on workflows."""

from typing import Optional, Tuple
import subprocess
import platform
import urllib.request
import os
import json

from ..rule import Rule
from ..models.workflow import Workflow
from ..utils import LintLevels, Settings


def install_actionlint(platform_system: str, version: str) -> Tuple[bool, str]:
    """If actionlint is not installed, detects OS platform
    and installs actionlint"""

    error = f"An error occurred when installing Actionlint on {platform_system}"
    if platform_system.startswith("Linux"):
        return install_actionlint_source(error, version)
    elif platform_system == "Darwin":
        return install_actionlint_source(error, version) # Homebrew does not maintain previous versions of Actionlint
    elif platform_system.startswith("Win"):
        try:
            subprocess.run(["choco", "install", "actionlint", "-y", f"--version='{version}'"], check=True)
            return True, ""
        except (FileNotFoundError, subprocess.CalledProcessError):
            return False, f"{error} : check Choco installation"
    return False, error

def load_config() -> dict:
    """Load configuration from a JSON file."""
    config_path = os.path.join(os.path.dirname(__file__), "../../../actionlint_version.json")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with open(config_path, "r") as config_file:
        return json.load(config_file)

def install_actionlint_source(error, version) -> Tuple[bool, str]:
    """Install Actionlint Binary from provided script"""
    url = "https://raw.githubusercontent.com/rhysd/actionlint/main/scripts/download-actionlint.bash"
    version = version
    request = urllib.request.urlopen(url)
    with open("download-actionlint.bash", "wb+") as fp:
        fp.write(request.read())
    try:
        subprocess.run(["bash", "download-actionlint.bash", version], check=True)
        return True, "./actionlint"
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False, error

def check_actionlint_path(platform_system: str, version: str) -> Tuple[bool, str]:
    """Check if the actionlint is in the system's PATH."""
    try:
        installed = subprocess.run(
            ["actionlint", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            )
        if version in f"{installed}":
            return True, ""
        else:
            return install_actionlint(platform_system, version)

    except subprocess.CalledProcessError:
        return (
            False,
            "Failed to install Actionlint, \
please check your package installer or manually install it",
        )
    except FileNotFoundError:
        return check_actionlint_local(platform_system, version)

def check_actionlint_local(platform_system: str, version: str) -> Tuple[bool, str]:

        try:
            installed = subprocess.run(
            ["./actionlint", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            )
            if version in f"{installed}":
                return True, "./actionlint"
            else:
                return install_actionlint(platform_system, version)
        except FileNotFoundError:
                return install_actionlint(platform_system, version)

class RunActionlint(Rule):
    """Rule to run actionlint as part of workflow linter V2."""

    def __init__(self, settings: Optional[Settings] = None, lint_level: Optional[LintLevels] = LintLevels.NONE) -> None:
        self.message = "Actionlint must pass without errors"
        self.on_fail = lint_level
        self.compatibility = [Workflow]
        self.settings = settings

    def fn(self, obj: Workflow) -> Tuple[bool, str]:
        if not obj or not obj.filename:
            raise AttributeError(
                "Running actionlint without a filename is not currently supported"
            )
    
        config = load_config()
        if "actionlint_version" not in config:
            raise KeyError("The 'actionlint_version' is missing in the configuration file.")
        version = config["actionlint_version"]

        installed, location = check_actionlint_path(platform.system(), version)
        if installed:
            if location:
                result = subprocess.run(
                    [location, obj.filename],
                    capture_output=True,
                    text=True,
                    check=False,
                )
            else:
                result = subprocess.run(
                    ["actionlint", obj.filename],
                    capture_output=True,
                    text=True,
                    check=False,
                )
            if result.returncode == 1:
                return False, result.stdout
            if result.returncode > 1:
                return False, result.stdout
            return True, ""
        else:
            return False, self.message
