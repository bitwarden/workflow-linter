"""A Rule to run actionlint on workflows."""

from typing import Optional, Tuple
import subprocess
import platform
import urllib.request

from ..rule import Rule
from ..models.workflow import Workflow
from ..utils import LintLevels, Settings


def install_actionlint(version: str) -> str:
    """
    Attempts to install actionlint on the system.

    Parameters:
    version (str): The version of actionlint to install.

    Returns:
    str: The location of the actionlint executable.
    """

    platform_system = platform.system().lower()
    platform_arch = platform.machine().lower()

    # Set defaults assuming Darwin/Linux
    decompress_command = ["tar", "-xzf"]
    file_extension = "tar.gz"

    # If the system is Windows, update values
    if platform_system == "windows":
        decompress_command = ["tar", "-xf"]
        file_extension = "zip"

    filename = (
        f"actionlint_{version}_{platform_system}_{platform_arch}.{file_extension}"
    )
    url = f"https://github.com/rhysd/actionlint/releases/download/v{version}/{filename}"
    request = urllib.request.urlopen(url)
    with open(filename, "wb+") as fp:
        fp.write(request.read())

    error = f"An error occurred when installing Actionlint on {platform_system} ({platform_arch})."
    try:
        decompress_command.append(filename)
        result = subprocess.run(decompress_command, check=False)
        if result.returncode != 0:
            print(f"Result: {result.returncode}")
            raise Exception(error)
    except Exception as e:
        print(e)
        raise Exception(error)

    return "./actionlint"


def get_actionlint_location(version: str) -> str:
    """
    Checks the system path and current directory to see if actionlint is already installed.

    Parameters:
    version (str): The version of actionlint to check for.

    Returns:
    tuple(bool, str): The bool represents if actionlint is installed, the string is the location of the executable.
    """

    # Check if actionlint is installed in the current directory.
    try:
        installed = subprocess.run(
            ["./actionlint", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if version in f"{installed}":
            return "./actionlint"
    except:
        pass

    # Check if actionlint is installed in the system PATH.
    try:
        installed = subprocess.run(
            ["actionlint", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if version in f"{installed}":
            return "actionlint"
    except:
        pass

    raise FileNotFoundError


class RunActionlint(Rule):
    """Rule to run actionlint as part of workflow linter V2."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        lint_level: Optional[LintLevels] = LintLevels.NONE,
    ) -> None:
        self.message = "Actionlint must pass without errors"
        self.on_fail = lint_level
        self.compatibility = [Workflow]
        self.settings = settings

    def fn(self, obj: Workflow) -> Tuple[bool, str]:
        if not obj or not obj.filename:
            raise AttributeError(
                "Running actionlint without a filename is not currently supported"
            )

        if not self.settings.actionlint_version:
            raise KeyError(
                "The 'actionlint_version' is missing in the configuration file."
            )

        # Check if actionlint is installed and the location of the executable
        try:
            executable_location = get_actionlint_location(
                self.settings.actionlint_version
            )
        except FileNotFoundError:
            executable_location = install_actionlint(self.settings.actionlint_version)

        result = subprocess.run(
            [executable_location, obj.filename],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return False, result.stdout
        return True, ""
