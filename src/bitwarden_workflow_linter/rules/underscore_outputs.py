""" Rule to enforce all GitHub outputs with more than one words use an underscore."""

import re

from typing import Optional, Union, Tuple

from ..models.job import Job
from ..rule import Rule
from ..models.workflow import Workflow
from ..models.step import Step
from ..utils import LintLevels, Settings


class RuleUnderscoreOutputs(Rule):
    """Rule to enforce all GitHub outputs with more than one word use an underscore.

    A simple standard to ensure uniformity in naming.
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
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
        """Enforces all outputs to have an underscore in the key name.

        This Rule checks all outputs in a Workflow, Job, or Step to ensure that
        the key name contains an underscore. This is to ensure that the naming
        convention is consistent across all outputs in the workflow configuration

        Example:
        ---
        on:
          workflow_dispatch:
            outputs:
              registry:
                value: 'Test Value'
              some_registry:
                value: 'Test Value'
          workflow_call:
            outputs:
              registry:
                value: 'Test Value'
              some_registry:
                value: 'Test Value'
        jobs:
          job-key:
            runs-on: ubuntu-22.04
            outputs:
              test_key_job: ${{ steps.test_output_1.outputs.test_key }}
            steps:
              - name: Test output in one-line run step
                id: test_output_1
                run: echo "test_key_1=Test-Value1" >> $GITHUB_OUTPUT

              - name: Test output in multi-line run step
                id: test_output_2
                run: |
                  echo
                  fake-command=Test-Value2
                  echo "test_key_2=$REF" >> $GITHUB_OUTPUT
                  echo "deployed_ref=$DEPLOYED_REF" >> $GITHUB_OUTPUT

              - name: Test step with no run
                id: test_output_3
                uses: actions/checkout@v2
                with:
                  ref: ${{ github.ref }}
                  fetch-depth: 0

        In this example, in workflow level 'registry' and 'some_registry' are outputs
        that satisfy the rule in both 'workflow_dispatch' and 'workflow_call' events.
        In job level 'test_key_job' satisfies the rule.
        In step level 'test_key_1', 'test_key_2', and 'deployed_ref' satisfy the rule.

        See tests/rules/test_underscore_outputs.py for incorrect examples.
        """

        outputs = []

        if isinstance(obj, Workflow):
            if obj.on.get("workflow_dispatch"):
                if obj.on["workflow_dispatch"].get("outputs"):
                    outputs.extend(obj.on["workflow_dispatch"]["outputs"].keys())

            if obj.on.get("workflow_call"):
                outputs.extend(obj.on["workflow_call"]["outputs"].keys())

        if isinstance(obj, Job):
            if obj.outputs:
                outputs.extend(obj.outputs.keys())

        if isinstance(obj, Step):
            if obj.run:
                outputs.extend(
                    re.findall(
                        r"\b([a-zA-Z0-9_-]+)\s*=\s*[^=]*>>\s*\$GITHUB_OUTPUT", obj.run
                    )
                )

        for output_name in outputs:
            if "-" in output_name:
                return False, (
                    f"Hyphen found in {obj.__class__.__name__} output: {output_name}"
                )

        return True, ""
