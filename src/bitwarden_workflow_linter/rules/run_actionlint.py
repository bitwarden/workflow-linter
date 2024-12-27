from typing import Union, Tuple
import subprocess

from ..rule import Rule
from ..models.job import Job
from ..models.workflow import Workflow
from ..models.step import Step
from ..utils import LintLevels, Settings


class RunActionlint(Rule):
    def __init__(self, settings: Settings = None) -> None:
        self.message = "Actionlint must pass without errors"
        self.on_fail: LintLevels = LintLevels.ERROR
        self.compatibility: List[Union[Workflow, Job, Step]] = [Job]
        self.settings: Settings = settings

    def fn(self, obj: Job) -> Tuple[bool, str]:
        result = subprocess.run(["actionlint"], capture_output=True, text=True)
        if result.returncode == 1:
            print(result.stdout)
            return False, self.message
        elif result.returncode > 1:
            return False, result.stderr
        return True, ""