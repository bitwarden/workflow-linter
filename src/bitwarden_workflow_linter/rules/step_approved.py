"""A Rule to enforce the use of a list of pre-approved Actions."""

from typing import Optional, Tuple

from ..models.step import Step
from ..rule import Rule
from ..utils import LintLevels, Settings


class RuleStepUsesApproved(Rule):
    """Rule to enforce that all Actions have been pre-approved.

    To limit the surface area of a supply chain attack in our pipelines, all Actions
    are required to pass a security review and be added to the pre-approved list to
    check against.
    """

    def __init__(self, settings: Optional[Settings] = None, lint_level: Optional[LintLevels] = LintLevels.NONE) -> None:
        """Constructor for RuleStepUsesApproved to override Rule class.

        Args:
          settings:
            A Settings object that contains any default, overridden, or custom settings
            required anywhere in the application.
          lint_level:
            The LintLevels enum value to determine the severity of the rule.
        """
        self.on_fail = lint_level
        self.compatibility = [Step]
        self.settings = settings

    def skip(self, obj: Step) -> bool:
        """Skip this Rule on some Steps.

        This Rule does not apply to a few types of Steps. These
        Rules are skipped.
        """
        ## Force pass for any shell steps
        if not obj.uses:
            return True

        ## Force pass for any local actions
        if "@" not in obj.uses:
            return True

        ## Force pass for any bitwarden/
        if obj.uses.startswith("bitwarden/"):
            return True

        return False

    def fn(self, obj: Step) -> Tuple[bool, str]:
        """Enforces all externally used Actions are on the pre-approved list.

        The pre-approved list allows tight auditing on what Actions are trusted
        and allowed to be run in our environments. This helps mitigate risks
        against supply chain attacks in our pipelines.

        Example:
        ---
        on:
          workflow_dispatch:

        jobs:
          job-key:
            runs-on: ubuntu-22.04
            steps:
              - name: Checkout Branch
                uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1

              - name: Test Bitwarden Action
                uses: bitwarden/gh-actions/get-keyvault-secrets@main

              - name: Test Local Action
                uses: ./actions/test-action

              - name: Test Run Action
                run: echo "test"

        In this example, 'actions/checkout' must be on the pre-approved list
        and the metadata must match in order to succeed. The other three
        Steps will be skipped.
        """
        if self.skip(obj):
            return True, ""

        obj_path = obj.uses_path

        # Remove the action directory if the action is in a multi-actions repo
        if len(obj.uses_path.split("/")) > 2:
            obj_path = "/".join(obj.uses_path.split("/")[:-1])

        # Actions in bitwarden/ are auto-approved
        if obj.uses and not obj_path in self.settings.approved_actions:
            return False, (
                f"New Action detected: {obj.uses_path}\nFor security purposes, "
                "actions must be reviewed and be on the pre-approved list"
            )

        return True, ""
