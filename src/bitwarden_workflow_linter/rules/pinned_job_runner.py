"""A Rule to enforce pinning runners to a specific OS version."""

from typing import Optional, Tuple

from ..models.job import Job
from ..rule import Rule
from ..utils import LintLevels, Settings


class RuleJobRunnerVersionPinned(Rule):
    """Rule to enforce pinned Runner OS versions.

    Using `*-latest` versions will update automatically and has broken all of
    our workflows in the past. To avoid this and prevent a single event from
    breaking the majority of our pipelines, we pin the versions.
    """

    def __init__(self, settings: Optional[Settings] = None, lint_level: Optional[LintLevels] = LintLevels.NONE) -> None:
        """Constructor for RuleJobRunnerVersionPinned to override Rule class.

        Args:
          settings:
            A Settings object that contains any default, overridden, or custom settings
            required anywhere in the application.
          lint_level:
            The LintLevels enum value to determine the severity of the rule.
        """
        self.message = "Workflow runner must be pinned"
        self.on_fail = lint_level
        self.compatibility = [Job]
        self.settings = settings

    def fn(self, obj: Job) -> Tuple[bool, str]:
        """Enforces runners are pinned to a version

        Example:
        ---
        on:
          workflow_dispatch:

        jobs:
          job-key:
            runs-on: ubuntu-22.04
            steps:
              - run: echo test

        call-workflow:
          uses: bitwarden/server/.github/workflows/workflow-linter.yml@master

        'runs-on' is pinned to '22.04' instead of 'latest'
        """
        if obj.runs_on is not None and "latest" in obj.runs_on:
            return False, self.message
        return True, ""
