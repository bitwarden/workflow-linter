"""A Rule to run actionlint on workflows."""

from typing import Optional, Tuple
import subprocess
import platform
import urllib.request
import urllib.error
import os
import tarfile
import io
import hashlib

from ..rule import Rule
from ..models.workflow import Workflow
from ..utils import LintLevels, Settings


_CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "bwwl")


def install_actionlint(platform_system: str, version: str) -> Tuple[bool, str]:
    """If actionlint is not installed, detects OS platform
    and installs actionlint"""

    error = f"An error occurred when installing Actionlint on {platform_system}"

    if platform_system.startswith(("Linux", "Darwin")):
        """Homebrew does not maintain non-latest versions of actionlint so Mac will install from source"""
        return install_actionlint_source(error,version)
    elif platform_system.startswith("Win"):
        try:
            subprocess.run(["choco", "install", "actionlint", "-y", f"--version='{version}'"], check=True)
            return True, ""
        except (FileNotFoundError, subprocess.CalledProcessError):
            return False, f"{error} : check Choco installation"
    return False, error


def _verify_checksum(data: bytes, filename: str, version: str) -> bool:
    """Verify SHA256 of downloaded tarball against the published checksums file."""
    checksum_url = f"https://github.com/rhysd/actionlint/releases/download/v{version}/actionlint_{version}_checksums.txt"
    try:
        checksums = urllib.request.urlopen(checksum_url, timeout=30).read().decode()
    except (urllib.error.URLError, OSError):
        return False
    for line in checksums.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] == filename:
            return hashlib.sha256(data).hexdigest() == parts[0]
    return False


def install_actionlint_source(error, version) -> Tuple[bool, str]:
    """Download and install actionlint binary directly from GitHub releases."""
    system = platform.system().lower()
    arch_map = {"x86_64": "amd64", "aarch64": "arm64", "arm64": "arm64"}
    arch = arch_map.get(platform.machine().lower(), platform.machine().lower())
    filename = f"actionlint_{version}_{system}_{arch}.tar.gz"
    url = f"https://github.com/rhysd/actionlint/releases/download/v{version}/{filename}"
    binary_path = os.path.join(_CACHE_DIR, "actionlint")
    os.makedirs(_CACHE_DIR, exist_ok=True)
    try:
        data = urllib.request.urlopen(url, timeout=30).read()
        if not _verify_checksum(data, filename, version):
            return False, f"{error} : checksum verification failed"
        with tarfile.open(fileobj=io.BytesIO(data)) as tar:
            member = next((m for m in tar.getmembers() if m.name == "actionlint"), None)
            if member is None:
                return False, error
            src = tar.extractfile(member)
            if src is None:
                return False, error
            with src, open(binary_path, "wb") as dst:
                dst.write(src.read())
        os.chmod(binary_path, 0o755)
        return True, binary_path
    except (urllib.error.URLError, tarfile.TarError, OSError):
        return False, error


def check_actionlint_path(platform_system: str, version: str) -> Tuple[bool, str]:
    """Check if the actionlint is in the system's PATH."""
    try:
        installed = subprocess.run(
            ["actionlint", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        if version in installed.stdout:
            return True, ""
        else:
            return install_actionlint(platform_system, version)
    except subprocess.CalledProcessError:
        return (
            False,
            "Failed to install Actionlint, \
please check your package installer or manually install it",
        )
    except FileNotFoundError:
        return check_actionlint_local(platform_system, version)

def check_actionlint_local(platform_system: str, version: str) -> Tuple[bool, str]:
    local_path = os.path.join(_CACHE_DIR, "actionlint")
    try:
        installed = subprocess.run(
            [local_path, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        if version in installed.stdout:
            return True, local_path
        else:
            return install_actionlint(platform_system, version)
    except FileNotFoundError:
        return install_actionlint(platform_system, version)


class RunActionlint(Rule):
    """Rule to run actionlint as part of workflow linter V2."""

    def __init__(self, settings: Optional[Settings] = None, lint_level: Optional[LintLevels] = LintLevels.NONE) -> None:
        self.message = "Actionlint must pass without errors"
        self.on_fail = lint_level
        self.compatibility = [Workflow]
        self.settings = settings

    def fn(self, obj: Workflow) -> Tuple[bool, str]:
        if not obj or not obj.filename:
            raise AttributeError(
                "Running actionlint without a filename is not currently supported"
            )

        if not self.settings.actionlint_version:
            raise KeyError("The 'actionlint_version' is missing in the configuration file.")

        """Check if Actionlint is alerady installed and if it is installed somewhere not on the PATH (location)"""
        installed, location = check_actionlint_path(platform.system(), self.settings.actionlint_version)
        if installed:
            if location:
                result = subprocess.run(
                     [location, obj.filename],
                    capture_output=True,
                    text=True,
                    check=False,
                )
            else:
                result = subprocess.run(
                    ["actionlint", obj.filename],
                    capture_output=True,
                    text=True,
                    check=False,
                )
            if result.returncode != 0:
                return False, result.stdout
            return True, ""
        else:
            return False, self.message
