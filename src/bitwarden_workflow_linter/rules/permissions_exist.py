"""A Rule to enforce that the required permissions are specified on every workflow"""

from typing import Optional, Tuple

from ..models.workflow import Workflow
from ..rule import Rule
from ..utils import LintLevels, Settings


class RulePermissionsExist(Rule):
    """
    Rule to enforce that the required permissions are specified on every workflow.

    To allow for keeping repository default GITHUB_TOKEN permissions to a minimum,
    each workflow must specify the permissions block (including read).

    This has 2 benefits:
    1) When changing the default repository setting to a more restrictive one,
       the workflows will not be affected.
    2) It is clear to the user what permissions are required for the workflow to run.
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        lint_level: Optional[LintLevels] = LintLevels.NONE,
    ) -> None:
        self.message = (
            "A top-level permissions section must be configured in the workflow."
        )
        self.on_fail = lint_level
        self.compatibility = [Workflow]
        self.settings = settings

    def permissions_exist(self, obj: Workflow) -> bool:
        if obj.permissions is None:
            return False
        return True

    def fn(self, obj: Workflow) -> Tuple[bool, str]:
        if not self.permissions_exist(obj):
            return False, f"{self.message}"
        return True, ""
