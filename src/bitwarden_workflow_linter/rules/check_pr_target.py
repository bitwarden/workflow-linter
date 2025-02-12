"""A Rule to enforce check-run is run when workflow uses pull_request_target."""

from typing import Optional, Tuple

from ..models.workflow import Workflow
from ..rule import Rule
from ..utils import LintLevels, Settings


class RuleCheckPrTarget(Rule):
    def __init__(self, settings: Optional[Settings] = None, lint_level: Optional[LintLevels] = LintLevels.NONE) -> None:
        """
        To ensure pull_request_target is safe to use, the check-run step is added
        to all jobs as a dependency.

        Once a branch is pushed to Github, it already opens up a vulnerability
        even if the check-run scan fails to detect this.

        In order to prevent a vulnerable branch from being used for an attack
        prior to being caught through vetting, all pull_request_target workflows
        should only be run by users with appropriate permissions.

        This greatly reduces the risk as community contributors can't use a fork to run a compromised workflow that uses pull_request_target.
        """
        self.message = "A check-run job must be included as a direct job dependency when pull_request_target is used and the workflow may only apply to runs on the main branch"
        self.on_fail = lint_level
        self.compatibility = [Workflow]
        self.settings = settings

    def targets_main_branch(self, obj:Workflow) -> bool:
        if obj.on["pull_request_target"].get("branches"):
            branches_list = obj.on["pull_request_target"].get("branches")
            if isinstance(branches_list, str):
                branches_list = [branches_list]
            if any(branch != 'main' for branch in branches_list):
                return False
        else:
            return False
        return True

    def has_check_run(self, obj: Workflow) -> Tuple[bool, str]:
        for name, job in obj.jobs.items():
            if job.uses == "bitwarden/gh-actions/.github/workflows/check-run.yml@main":
                return True, name
        return False, ""

    def check_run_required(self, obj:Workflow, check_job:str) -> list:
        missing_jobs = []
        for job in list(obj.jobs.keys()):
            if job is not check_job:
                job_list = obj.jobs[job].needs
                if job_list:
                    if check_job not in job_list:
                        missing_jobs.append(job)
                else:
                    missing_jobs.append(job)
        return missing_jobs

    def fn(self, obj: Workflow) -> Tuple[bool, str]:
        Errors = []
        if obj.on.get("pull_request_target"):
            result, check_job = self.has_check_run(obj)
            main_branch_only = self.targets_main_branch(obj)
            if not main_branch_only:
                Errors.append("Workflows using pull_request_target can only target the main branch")
            if result:
                missing_jobs = self.check_run_required(obj, check_job)
                if missing_jobs:
                    job_list = ', '.join(missing_jobs)
                    message = f"Check-run is missing from the following jobs in the workflow: {job_list}"
                    Errors.append(message)
            else:
                message = f"A check-run job must be included as a direct job dependency when pull_request_target is used"
                Errors.append(message)
            if Errors:
                self.message = "\n".join(Errors)
                return False, f"{self.message}"
            else:
                return True, ""
        else:
            return True, ""
