"""A Rule to enforce prefixes environment variables."""

from typing import Optional, Tuple

from ..models.job import Job
from ..rule import Rule
from ..utils import LintLevels, Settings


class RuleJobEnvironmentPrefix(Rule):
    """Rule to enforce specific prefixes for environment variables.

    Automated testing is not easily written for GitHub Action Workflows. CI can also
    get complicated really quickly and take up hundreds of lines. All of this can
    make it very difficult to debug and troubleshoot, especially when environment
    variables can be set in four different places: Workflow level, Job level, Step
    level, and inside a shell Step.

    To alleviate some of the pain, we have decided that all Job level environment
    variables should be prefixed with an underscore. All Workflow environment
    variables are normally at the top of the file and Step level ones are pretty
    visible when debugging a shell Step.
    """

    def __init__(self, settings: Optional[Settings] = None, lint_level: Optional[LintLevels] = LintLevels.NONE) -> None:
        """RuleJobEnvironmentPrefix constructor to override the Rule class.

        Args:
          settings:
            A Settings object that contains any default, overridden, or custom settings
            required anywhere in the application.
          lint_level:
            The LintLevels enum value to determine the severity of the rule.
        """
        self.message = "Job environment vars should start with an underscore:"
        self.on_fail = lint_level
        self.compatibility = [Job]
        self.settings = settings

    def fn(self, obj: Job) -> Tuple[bool, str]:
        """Enforces the underscore prefix standard on job envs.

        Example:
        ---
        on:
          workflow_dispatch:

        jobs:
          job-key:
            runs-on: ubuntu-22.04
            env:
                _TEST_ENV: "test"
            steps:
              - run: echo test

        All keys under jobs.job-key.env should be prefixed with an underscore
        as in _TEST_ENV.

        See tests/rules/test_job_environment_prefix.py for examples of
        incorrectly named environment variables.
        """
        correct = True
        allowed_envs = {
            "NODE_OPTIONS",
            "NUGET_PACKAGES",
            "MINT_PATH",
            "MINT_LINK_PATH",
            "HUSKY",
        }

        if obj.env:
            offending_keys = []
            for key in obj.env.keys():
                if key not in allowed_envs and key[0] != "_":
                    offending_keys.append(key)
                    correct = False

        if correct:
            return True, ""

        return False, f"{self.message} ({', '.join(offending_keys)})"
