# Bitwarden Workflow Linter

Bitwarden's Workflow Linter is an extensible linter to apply opinionated organization-specific GitHub Action standards. It was designed to be used alongside [yamllint](https://github.com/adrienverge/yamllint) to enforce specific YAML standards.

To see an example of Workflow Linter in practice in GitHub Action, see the [composite Action](https://github.com/bitwarden/gh-actions/tree/main/lint-workflow).

## Prerequisites

- Python 3.12
- pipenv
- Windows systems: Chocolatey package manager
- Mac OS systems: Homebrew package manager
- pipx

## Setup

1. **Create the virtual environment:**
   ```bash
   python3.12 -m venv /Users/$USER/bitwarden_workflow_linter_venv
   ```

2. **Activate the virtual environment:**
   ```bash
   source /Users/$USER/bitwarden_workflow_linter_venv/bin/activate
   ```

## Installation

### From PyPI
This is the recommended method for most users. Installing from PyPI ensures you get the latest stable release and is the easiest way to install and update the package.


1. **Install Bitwarden Workflow Linter:**
   ```bash
   pip install --upgrade bitwarden_workflow_linter
   ```

2. **Deactivate the virtual environment (optional):**
   ```bash
   deactivate
   ```
#### Using pipx

Alternatively, you can install `bwwl` globally using `pipx` to keep it isolated:

1. **Install Bitwarden Workflow Linter:**
   ```bash
   pipx install bitwarden_workflow_linter --python python3.12
   ```

This method is ideal for running `bwwl` as a standalone CLI tool without managing a virtual environment manually.

### From GitHub Release
Use this method if you need a specific version of the package that is not yet available on PyPI, or if you want to access pre-release versions.

1. **Download the release tarball or zip file from GitHub:**
   ```bash
   wget https://github.com/bitwarden/workflow-linter/archive/refs/tags/vX.Y.Z.tar.gz
   tar -xzf vX.Y.Z.tar.gz
   cd workflow-linter-X.Y.Z
   ```

2. **Install the package:**
   ```bash
   pip install .
   ```

3. **Deactivate the virtual environment (optional):**
   ```bash
   deactivate
   ```

### Locally
This method is useful for developers who want to contribute to the project or need to make local modifications to the source code. *Make sure to follow the virtual environment prerequisite setup*
1. **Clone the repository:**
   ```bash
   git clone git@github.com:bitwarden/workflow-linter.git
   cd workflow-linter
   ```

2. **Install the package:**
   ```bash
   pip install -e .
   ```

3. **Deactivate the virtual environment (optional):**
   ```bash
   deactivate
   ```

## Usage

### Setup settings.yaml

If a non-default configuration is desired (different than `src/bitwarden_workflow_linter/default_settings.yaml`), copy the below and create a `settings.yaml` in the directory that `bwwl` will be running from.

```yaml
enabled_rules:
    - id: bitwarden_workflow_linter.rules.name_exists.RuleNameExists
      level: error
    - id: bitwarden_workflow_linter.rules.name_capitalized.RuleNameCapitalized
      level: error
    - id: bitwarden_workflow_linter.rules.pinned_job_runner.RuleJobRunnerVersionPinned
      level: error
    - id: bitwarden_workflow_linter.rules.job_environment_prefix.RuleJobEnvironmentPrefix
      level: error
    - id: bitwarden_workflow_linter.rules.step_pinned.RuleStepUsesPinned
      level: error
    - id: bitwarden_workflow_linter.rules.underscore_outputs.RuleUnderscoreOutputs
      level: warning
    - id: bitwarden_workflow_linter.rules.run_actionlint.RunActionlint
      level: warning

approved_actions_path: default_actions.json
```

### Command Line Usage

```bash
usage: bwwl [-h] [-v] {lint,actions} ...

positional arguments:
  {lint,actions}
    lint          Verify that a GitHub Action Workflow follows all of the Rules.
    actions       Add or Update Actions in the pre-approved list.

options:
  -h, --help      show this help message and exit
  -v, --verbose
```
## Pre-commit Hook Setup

### Navigate to the `.git/hooks` directory in the repository you wish to lint:

```bash
cd .git/hooks
```

### Create the `pre-commit` file (if it does not already exist):

```bash
touch pre-commit
```

### Make the script executable:

```bash
chmod +x pre-commit
```

### Edit the `pre-commit` script:

Open the `pre-commit` file with your favorite text editor and add the following content, replacing `/Users/$USER/bitwarden_workflow_linter_venv/bin/activate` with the actual path to your virtual environment:

```bash
#!/bin/bash
set -e
# Activate the virtual environment
source "/Users/$USER/bitwarden_workflow_linter_venv/bin/activate"
# Get the repository root directory
repo_root=$(git rev-parse --show-toplevel)
# Run your Python script
bwwl lint -f "$repo_root/.github/workflows"
# Deactivate the virtual environment (optional)
deactivate
```

### Test the Hook:

Try committing a change to the repository. The pre-commit hook should run the workflow linter.

## Development

### Setup
Refer to the [Locally](#locally) instructions above to clone the repository and install the package.

### Testing

All built-in `src/bitwarden_workflow_linter/rules` should have 100% code coverage and we should shoot for an overall coverage of 80%+. We are lax on the [imperative shell](https://www.destroyallsoftware.com/screencasts/catalog/functional-core-imperative-shell) (code interacting with other systems; ie. disk, network, etc), but we strive to maintain a high coverage over the functional core (objects and models).

```bash
pipenv shell
pytest tests --cov=src
```

### Code Reformatting

We adhere to PEP8 and use `black` to maintain this adherence. `black` should be run on any change being merged to `main`.

```bash
pipenv shell
black .
```

### Linting

We loosely use [Google's Python style guide](https://google.github.io/styleguide/pyguide.html), but yield to `black` when there is a conflict.

```bash
pipenv shell
pylint --rcfile pylintrc src/ tests/
```

### Add a new Rule

A new Rule is created by extending the Rule base class and overriding the `fn(obj: Union[Workflow, Job, Step])` method. Available attributes of `Workflows`, `Jobs` and `Steps` can be found in their definitions under `src/models`.

For a simple example, we'll take a look at enforcing the existence of the `name` key in a Job. This is already done by default with the `src.rules.name_exists.RuleNameExists`, but provides a simple enough example to walk through.

```python
from typing import Union, Tuple

from ..rule import Rule
from ..models.job import Job
from ..models.workflow import Workflow
from ..models.step import Step
from ..utils import LintLevels, Settings


class RuleJobNameExists(Rule):
    def __init__(self, settings: Settings = None, lint_level: Optional[LintLevels] = LintLevels.ERROR) -> None:
        self.message = "name must exist"
        self.on_fail: LintLevels = lint_level
        self.compatibility: List[Union[Workflow, Job, Step]] = [Job]
        self.settings: Settings = settings

    def fn(self, obj: Job) -> Tuple[bool, str]:
        """<doc block goes here> """
        if obj.name is not None:
            return True, ""
        return False, self.message
```

By default, a new Rule needs five things:

- `self.message`: The message to return to the user on a lint failure
- `self.on_fail`: The level of failure on a lint failure (NONE, WARNING, ERROR). NONE and WARNING will exit with a code of 0 (unless using `strict` mode for WARNING). ERROR will exit with a non-zero exit code
- `self.compatibility`: The list of objects this rule is compatible with. This is used to create separate instances of the Rule for each object in the Rules collection.
- `self.settings`: In general, this should default to what is shown here, but allows for overrides
- `self.fn`: The function doing the actual work to check the object and enforce the standard.

`fn` can be as simple or as complex as it needs to be to run a check on a _single_ object. This linter currently does not support Rules that check against multiple objects at a time OR file level formatting (one empty between each step or two empty lines between each job).

_IMPORTANT: A rule must be implemented and tested then merged into `main` before it can be activated._ This is because the released version of `bwwl` will use the current `settings.yaml` file, but it will not have the new rule functionality yet and cause an error in the workflow linting of this repository.

To activate a rule after implementing and releasing it, add it to `settings.yaml` in the project's base folder and `src/bitwarden_workflow_linter/default_settings.yaml` to make the rule default.

Before creating a new rule please read the [Workflow linter rule rollout process](./RULE_ROLLOUT.md) document in which you'll find the process for rolling out new workflow linter rules.
