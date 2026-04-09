"""A Rule to run zizmor on workflows."""

from typing import Optional, Tuple
import subprocess
import platform
import urllib.request
import urllib.error
import tempfile
import os

from ..rule import Rule
from ..models.workflow import Workflow
from ..utils import LintLevels, Settings


def install_zizmor(platform_system: str, version: str) -> Tuple[bool, str]:
    """Install zizmor via pip."""
    error = f"An error occurred when installing Zizmor on {platform_system}"
    try:
        subprocess.run(
            ["pip", "install", f"zizmor=={version}"], check=True, capture_output=True
        )
        return True, ""
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False, f"{error} : check pip installation"


def check_zizmor_path(platform_system: str, version: str) -> Tuple[bool, str]:
    """Check if zizmor is in the system's PATH."""
    try:
        result = subprocess.run(
            ["zizmor", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
        )
        installed_version = result.stdout.strip().split()[-1] if result.stdout else ""
        if version in installed_version:
            return True, ""
        else:
            return install_zizmor(platform_system, version)
    except subprocess.CalledProcessError:
        return (
            False,
            (
                "Failed to install zizmor, please check your pip "
                "installation or manually install it"
            ),
        )
    except FileNotFoundError:
        return install_zizmor(platform_system, version)


def download_config_content(config_url: str) -> Optional[str]:
    """Download zizmor config file content from remote URL."""
    if not config_url:
        return None

    try:
        with urllib.request.urlopen(config_url, timeout=30) as response:
            return response.read().decode("utf-8")
    except (urllib.error.URLError, IOError):
        return None


class RunZizmor(Rule):
    """Rule to run zizmor as part of workflow linter."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        lint_level: Optional[LintLevels] = LintLevels.WARNING,
    ) -> None:
        self.message = "Zizmor must pass without errors"
        self.on_fail = lint_level
        self.compatibility = [Workflow]
        self.settings = settings

    def fn(self, obj: Workflow) -> Tuple[bool, str]:
        if not obj or not obj.filename:
            raise AttributeError(
                "Running zizmor without a filename is not currently supported"
            )

        if not self.settings.zizmor_version:
            raise KeyError("The 'zizmor_version' is missing in the configuration file.")

        # Check if zizmor is already installed
        installed, error = check_zizmor_path(
            platform.system(), self.settings.zizmor_version
        )
        if not installed:
            return False, error

        cmd = ["zizmor", "--format", "plain"]

        with tempfile.TemporaryDirectory() as tmpdir:
            if self.settings.zizmor_config_url:
                config_content = download_config_content(self.settings.zizmor_config_url)
                if config_content:
                    config_file = os.path.join(tmpdir, "zizmor.yml")
                    with open(config_file, "w") as f:
                        f.write(config_content)
                    cmd.extend(["--config", config_file])

            cmd.append(obj.filename)

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False,
                )
            except (FileNotFoundError, OSError) as e:
                return False, f"Error running zizmor: {str(e)}"

        if result.returncode == 0:
            return True, ""
        output = result.stdout if result.stdout else result.stderr
        return False, output
