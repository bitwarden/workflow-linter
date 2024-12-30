from typing import Union, Tuple
import subprocess
import platform
import shutil

from ..rule import Rule
from ..models.job import Job
from ..models.workflow import Workflow
from ..models.step import Step
from ..utils import LintLevels, Settings


def check_actionlint():
    """Check if the actionlint is in the system's PATH."""
    Platform = platform.system()
    try:
        subprocess.run(["actionlint", '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        if Platform.startswith('Linux'):
            try:
                subprocess.run(['sudo', 'apt-get', 'install', '-y', 'actionlint'], check=True)
                return True
            except subprocess.CalledProcessError:
                print(f"Failed to install Actionlint. Please check your package manager or manually install it.")
                return False
        elif Platform == 'Darwin':
            try:
                subprocess.run(['brew', 'install', 'actionlint'], check=True)
                return True
            except subprocess.CalledProcessError:
                print(f"Failed to install Actionlint. Please check your Homebrew installation or manually install it.")
                return False
        elif Platform == 'Win32':
            try:
                subprocess.run(['choco', 'install', 'actionlint', '-y'], check=True)
                return True
            except subprocess.CalledProcessError:
                print(f"Failed to install Actionlint. Please check your Chocolatey installation or manually install it.")
                return False
            
class RunActionlint(Rule):
    def __init__(self, settings: Settings = None) -> None:
        self.message = "Actionlint must pass without errors"
        self.on_fail: LintLevels = LintLevels.WARNING
        self.compatibility = [Workflow, Job, Step]
        self.settings: Settings = settings

    def fn(self, obj: Job) -> Tuple[bool, str]:
        if check_actionlint():
            result = subprocess.run(["actionlint"], capture_output=True, text=True)
            if result.returncode == 1:
                print(result.stdout)
                return False, self.message
            elif result.returncode > 1:
                return False, result.stderr
            return True, ""
        else:
            print(f"Actionlint could not be installed.")
            return False, ""
