import re

from typing import Union, Tuple

from ..models.job import Job
from ..models.workflow import Workflow
from ..models.step import Step
from ..utils import LintLevels, Settings


class RuleUnderscoreOutputs:
    """Rule to enforce all GitHub 'outputs' more than one words contain an underscore.

    A simple standard to ensure uniformity in naming.
    """

    def __init__(self, settings: Settings = None) -> None:
        """Constructor for RuleUnderscoreOutputs to override the Rule class.

        Args:
          settings:
            A Settings object that contains any default, overridden, or custom settings
            required anywhere in the application.
        """
        self.message = "outputs with more than one word must use an underscore"
        self.on_fail = LintLevels.WARNING
        self.compatibility = [Workflow, Job, Step]
        self.settings = settings

    def fn(self, obj: Union[Workflow, Job, Step]) -> Tuple[bool, str]:
        outputs = []

        if isinstance(obj, Workflow):
            if obj.on.get("workflow_dispatch"):
                outputs.extend(obj.on["workflow_dispatch"]["outputs"].keys())

            if obj.on.get("workflow_call"):
                outputs.extend(obj.on["workflow_call"]["outputs"].keys())

        if isinstance(obj, Job):
            if obj.outputs:
                outputs.extend(obj.outputs.keys())

        if isinstance(obj, Step):
            if obj.run:
                outputs.extend(re.findall(r"\b([a-zA-Z0-9_-]+)\s*=\s*[^=]*>>", obj.run))

        for key in outputs:
            if "-" in key:
                return False, self.message

        return True, ""
