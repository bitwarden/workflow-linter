"""A Rule to run actionlint on workflows."""

from typing import Optional, Tuple
import subprocess
import platform
import urllib.request
import os

from ..rule import Rule
from ..models.workflow import Workflow
from ..utils import LintLevels, Settings


def install_actionlint(platform_system: str) -> Tuple[bool, str]:
    """If actionlint is not installed, detects OS platform
    and installs actionlint"""

    error = f"An error occurred when installing Actionlint on {platform_system}"

    if platform_system.startswith("Linux"):
        return install_actionlint_source(error)
    elif platform_system == "Darwin":
        try:
            subprocess.run(["brew", "install", "actionlint"], check=True)
            return True, ""
        except (FileNotFoundError, subprocess.CalledProcessError):
            return False, f"{error} : check Brew installation"
    elif platform_system.startswith("Win"):
        try:
            subprocess.run(["choco", "install", "actionlint", "-y"], check=True)
            return True, ""
        except (FileNotFoundError, subprocess.CalledProcessError):
            return False, f"{error} : check Choco installation"
    return False, error


def install_actionlint_source(error) -> Tuple[bool, str]:
    """Install Actionlint Binary from provided script"""
    url = "https://raw.githubusercontent.com/rhysd/actionlint/main/scripts/download-actionlint.bash"
    version = "1.6.17"
    request = urllib.request.urlopen(url)
    with open("download-actionlint.bash", "wb+") as fp:
        fp.write(request.read())
    try:
        subprocess.run(["bash", "download-actionlint.bash", version], check=True)
        return True, os.getcwd()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False, error


def check_actionlint(platform_system: str) -> Tuple[bool, str]:
    """Check if the actionlint is in the system's PATH."""
    try:
        subprocess.run(
            ["actionlint", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return True, ""
    except subprocess.CalledProcessError:
        return (
            False,
            "Failed to install Actionlint, \
please check your package installer or manually install it",
        )
    except FileNotFoundError:
        return install_actionlint(platform_system)


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

        installed, location = check_actionlint(platform.system())
        if installed:
            if location:
                result = subprocess.run(
                    [location + "/actionlint", obj.filename],
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
