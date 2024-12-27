from typing import Union, Tuple
import subprocess

from ..rule import Rule
from ..models.job import Job
from ..models.workflow import Workflow
from ..models.step import Step
from ..utils import LintLevels, Settings


class RunActionlint(Rule):
    def __init__(self, settings: Settings = None) -> None:
        self.message = "Actionlint must pass"
        self.on_fail: LintLevels = LintLevels.ERROR
        self.compatibility: List[Union[Workflow, Job, Step]] = [Job]
        self.settings: Settings = settings

    def fn(self, obj: Job) -> Tuple[bool, str]:
        result = subprocess.run(["actionlint"], capture_output=True, text=True)
        print(result.stdout)
        print(result.stderr)
        return True, self.message
