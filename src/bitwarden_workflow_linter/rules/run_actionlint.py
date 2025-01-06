"""A Rule to run actionlint on workflows."""

from typing import Optional, Tuple
import subprocess
import platform
import urllib.request

from ..rule import Rule
from ..models.workflow import Workflow
from ..utils import LintLevels, Settings

def check_actionlint():
    """Check if the actionlint is in the system's PATH.

    If actionlint is not installed, detects OS platform
    and installs actionlint
    """
    platform_system = platform.system()
    error = f"An unknown error occurred on platform {platform_system}"
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
        if platform_system.startswith("Linux"):
            url = "https://raw.githubusercontent.com/rhysd/actionlint/main/scripts/download-actionlint.bash"
            version = '1.6.17'
            request = urllib.request.urlopen(url)
            try:
                with open('download-actionlint.bash', 'wb+') as fp:
                    fp.write(request.read())
                    print("got to with open")
                    result = subprocess.run(
                        ['install-actionlint.bash', version], check=True, capture_output=True,
                    text=True,)
                    print('******')
                    print(result.stdout)
                    print('******')
                    return True, ""
            except (FileNotFoundError, subprocess.CalledProcessError):
                print(result.stdout)
                error = "Failed to install Actionlint1. \
Please check your package manager or manually install it."
                return False, error
        elif platform_system == "Darwin":
            try:
                subprocess.run(["brew", "install", "actionlint"], check=True)
                return True, ""
            except (FileNotFoundError, subprocess.CalledProcessError):
                error = "Failed to install Actionlint. \
Please check your Homebrew installation or manually install it."
                return False, error
        elif platform_system.startswith("Win"):
            try:
                subprocess.run(["choco", "install", "actionlint", "-y"], check=True)
                return True, ""
            except (FileNotFoundError, subprocess.CalledProcessError):
                error = "Failed to install Actionlint. \
Please check your Chocolatey installation or manually install it."
                return False, error
    return False, 'whoops'


class RunActionlint(Rule):
    """Rule to run actionlint as part of workflow linter V2."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.message = "Actionlint must pass without errors"
        self.on_fail = LintLevels.WARNING
        self.compatibility = [Workflow]
        self.settings = settings

    def fn(self, obj: Workflow) -> Tuple[bool, str]:
        if not obj.filename:
            raise NotImplementedError("Running actionlint without a filename is not currently supported")
        installed, install_error = check_actionlint()
        if installed:
            result = subprocess.run(
                ["actionlint", obj.filename],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 1:
                print(result.stdout)
                return False, self.message
            elif result.returncode > 1:
                return False, result.stderr
            return True, ""
        else:
            print(install_error)
            return False, install_error
