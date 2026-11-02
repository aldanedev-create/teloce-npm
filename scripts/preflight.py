#!/usr/bin/env python3
"""
Preflight checks for Teloce-NPM releases.

Verifies the repo is in a releasable state:
  - Git working tree is clean
  - Current branch is main/master
  - Version consistency (pyproject.toml == version.py)
  - Version not already on PyPI
  - CHANGELOG has an entry for the current version
  - Test suite passes
  - Linters pass (ruff, black, mypy)
  - Package builds cleanly (sdist + wheel)
  - Wheel contents are sane (no tests, no caches)
  - twine check passes (README renders on PyPI)

Exit code: 0 if all checks pass, 1 if any fail.

Usage:
    python scripts/preflight.py
    python scripts/preflight.py --skip-tests --skip-lint
    python scripts/preflight.py --fast            # skip tests, lint, install-test
    python scripts/preflight.py --verbose
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"
VERSION_FILE = REPO_ROOT / "src" / "teloce_npm" / "version.py"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
DIST_DIR = REPO_ROOT / "dist"

PACKAGE_NAME = "teloce-npm"           # PyPI distribution name
PYPI_JSON_URL = "https://pypi.org/pypi/{name}/json"
RELEASE_BRANCHES = {"main", "master"}

# Wheel contents that must NEVER be present
FORBIDDEN_WHEEL_PATTERNS = (
    "/tests/",
    "/examples/",
    "/benchmarks/",
    "/scripts/",
    "/docs/",
    ".venv/",
    "__pycache__/",
    ".pyc",
    ".pytest_cache/",
)


# ---------------------------------------------------------------------------
# ANSI colors
# ---------------------------------------------------------------------------
_USE_COLOR = sys.stdout.isatty()


def _c(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text


def ok(msg: str) -> str:    return _c(f"  ✓ {msg}", "92")
def fail(msg: str) -> str:  return _c(f"  ✗ {msg}", "91")
def warn(msg: str) -> str:  return _c(f"  ! {msg}", "93")
def info(msg: str) -> str:  return f"  · {msg}"
def header(msg: str) -> str: return _c(msg, "1;36")


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------
@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str = ""

    def __str__(self) -> str:
        if self.ok:
            line = ok(f"{self.name}")
        else:
            line = fail(f"{self.name}")
        if self.detail:
            for ln in self.detail.splitlines():
                line += "\n" + info(ln)
        return line


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def run(
    cmd: List[str],
    *,
    cwd: Path = REPO_ROOT,
    check: bool = False,
    capture: bool = True,
    verbose: bool = False,
) -> subprocess.CompletedProcess:
    """Run a subprocess, optionally capturing output."""
    if verbose:
        print(info("$ " + " ".join(cmd)))
    try:
        return subprocess.run(
            cmd,
            cwd=cwd,
            check=check,
            capture_output=capture,
            text=True,
        )
    except FileNotFoundError:
        raise RuntimeError(f"Command not found: {cmd[0]}")


def get_version_from_pyproject() -> str:
    """Read [project].version from pyproject.toml."""
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        try:
            import tomli as tomllib  # type: ignore
        except ImportError:
            raise RuntimeError(
                "Need tomli on Python < 3.11: pip install tomli"
            )
    with open(PYPROJECT, "rb") as f:
        data = tomllib.load(f)
    version = data.get("project", {}).get("version")
    if not version:
        raise RuntimeError("No [project].version in pyproject.toml")
    return version


def get_version_from_module() -> str:
    """Read __version__ from src/teloce_npm/version.py without importing."""
    content = VERSION_FILE.read_text(encoding="utf-8")
    match = re.search(
        r'^__version__\s*=\s*["\']([^"\']+)["\']',
        content,
        re.MULTILINE,
    )
    if not match:
        raise RuntimeError(f"No __version__ found in {VERSION_FILE}")
    return match.group(1)


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------
def check_git_repo() -> CheckResult:
    r = run(["git", "rev-parse", "--is-inside-work-tree"])
    if r.returncode != 0:
        return CheckResult("git_repo", False, "Not inside a git repository")
    return CheckResult("git_repo", True)


def check_git_clean() -> CheckResult:
    r = run(["git", "status", "--porcelain"])
    if r.returncode != 0:
        return CheckResult("git_clean", False, "git status failed")
    out = r.stdout.strip()
    if out:
        return CheckResult("git_clean", False, "Uncommitted changes:\n" + out)
    return CheckResult("git_clean", True, "working tree is clean")


def check_branch() -> CheckResult:
    r = run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    branch = r.stdout.strip()
    if branch not in RELEASE_BRANCHES:
        return CheckResult(
            "git_branch",
            False,
            f"on '{branch}', expected one of: {', '.join(sorted(RELEASE_BRANCHES))}",
        )
    return CheckResult("git_branch", True, f"on '{branch}'")


def check_version_consistency() -> CheckResult:
    try:
        v_pyproject = get_version_from_pyproject()
        v_module = get_version_from_module()
    except Exception as e:
        return CheckResult("version_consistency", False, str(e))

    if v_pyproject != v_module:
        return CheckResult(
            "version_consistency",
            False,
            f"pyproject.toml={v_pyproject!r} vs version.py={v_module!r}",
        )
    return CheckResult("version_consistency", True, f"version = {v_pyproject}")


def check_pypi_availability() -> CheckResult:
    try:
        version = get_version_from_pyproject()
    except Exception as e:
        return CheckResult("pypi_availability", False, str(e))

    url = PYPI_JSON_URL.format(name=PACKAGE_NAME)
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return CheckResult(
                "pypi_availability",
                True,
                f"{PACKAGE_NAME} is not on PyPI yet — first release",
            )
        return CheckResult(
            "pypi_availability", False, f"PyPI API returned HTTP {e.code}"
        )
    except urllib.error.URLError as e:
        return CheckResult(
            "pypi_availability", False, f"Network error: {e.reason}"
        )

    releases = data.get("releases", {})
    if version in releases:
        return CheckResult(
            "pypi_availability",
            False,
            f"version {version} is already published on PyPI",
        )
    return CheckResult(
        "pypi_availability", True, f"version {version} is available"
    )


def check_changelog_entry() -> CheckResult:
    if not CHANGELOG.exists():
        return CheckResult("changelog_entry", False, "CHANGELOG.md not found")

    try:
        version = get_version_from_pyproject()
    except Exception as e:
        return CheckResult("changelog_entry", False, str(e))

    content = CHANGELOG.read_text(encoding="utf-8")
    # Match "## [x.y.z]" or "## x.y.z"
    pattern = re.compile(
        r"^##\s+\[?" + re.escape(version) + r"\]?",
        re.MULTILINE,
    )
    if not pattern.search(content):
        return CheckResult(
            "changelog_entry",
            False,
            f"no '## [{version}]' section in CHANGELOG.md",
        )
    return CheckResult(
        "changelog_entry", True, f"found entry for {version}"
    )


def check_tests(verbose: bool = False) -> CheckResult:
    r = run([sys.executable, "-m", "pytest", "-q"], verbose=verbose)
    if r.returncode != 0:
        tail = (r.stdout or "")[-800:]
        return CheckResult("tests", False, tail.strip() or "pytest failed")
    return CheckResult("tests", True, "test suite passes")


def _run_linter(name: str, cmd: List[str], verbose: bool = False) -> CheckResult:
    r = run(cmd, verbose=verbose)
    if r.returncode != 0:
        tail = (r.stdout + r.stderr)[-600:].strip()
        return CheckResult(name, False, tail or f"{cmd[0]} exited {r.returncode}")
    return CheckResult(name, True)


def check_lint(verbose: bool = False) -> List[CheckResult]:
    results: List[CheckResult] = []
    results.append(_run_linter("ruff", [sys.executable, "-m", "ruff", "check", "."], verbose))
    results.append(_run_linter("black", [sys.executable, "-m", "black", "--check", "."], verbose))
    results.append(_run_linter("mypy", [sys.executable, "-m", "mypy", "src"], verbose))
    return results


def check_build(verbose: bool = False) -> CheckResult:
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    r = run(
        [sys.executable, "-m", "build", "--sdist", "--wheel"],
        verbose=verbose,
    )
    if r.returncode != 0:
        return CheckResult(
            "build", False, (r.stdout + r.stderr)[-800:].strip() or "build failed"
        )

    wheels = list(DIST_DIR.glob("*.whl"))
    sdists = list(DIST_DIR.glob("*.tar.gz"))
    if not wheels or not sdists:
        return CheckResult(
            "build", False, f"missing artifacts: {[p.name for p in DIST_DIR.iterdir()]}"
        )
    return CheckResult(
        "build",
        True,
        f"{len(wheels)} wheel(s), {len(sdists)} sdist(s)",
    )


def check_wheel_contents() -> CheckResult:
    wheels = list(DIST_DIR.glob("*.whl"))
    if not wheels:
        return CheckResult("wheel_contents", False, "no wheel found in dist/")

    bad_hits: List[str] = []
    with zipfile.ZipFile(wheels[0]) as zf:
        for name in zf.namelist():
            for pattern in FORBIDDEN_WHEEL_PATTERNS:
                if pattern in name:
                    bad_hits.append(name)
                    break

    if bad_hits:
        return CheckResult(
            "wheel_contents",
            False,
            "forbidden entries in wheel:\n" + "\n".join(bad_hits[:10]),
        )
    return CheckResult("wheel_contents", True, "wheel is clean")


def check_twine() -> CheckResult:
    artifacts = sorted(str(p) for p in DIST_DIR.iterdir() if p.is_file())
    if not artifacts:
        return CheckResult("twine_check", False, "no artifacts in dist/")
    r = run([sys.executable, "-m", "twine", "check", *artifacts])
    if r.returncode != 0:
        return CheckResult(
            "twine_check",
            False,
            (r.stdout + r.stderr)[-800:].strip() or "twine check failed",
        )
    return CheckResult("twine_check", True, "README renders correctly")


def check_install(verbose: bool = False) -> CheckResult:
    """
    Verify the built wheel installs and imports in a fresh venv.

    This catches missing package-data, broken metadata, and
    accidental dependencies on the source tree.
    """
    wheels = list(DIST_DIR.glob("*.whl"))
    if not wheels:
        return CheckResult("install_test", False, "no wheel found in dist/")

    try:
        expected_version = get_version_from_pyproject()
    except Exception as e:
        return CheckResult("install_test", False, str(e))

    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        venv_dir = Path(tmp) / "venv"
        r = run([sys.executable, "-m", "venv", str(venv_dir)], verbose=verbose)
        if r.returncode != 0:
            return CheckResult("install_test", False, "failed to create venv")

        pip = venv_dir / "bin" / "pip"
        python = venv_dir / "bin" / "python"
        if os.name == "nt":
            pip = venv_dir / "Scripts" / "pip.exe"
            python = venv_dir / "Scripts" / "python.exe"

        r = run([str(pip), "install", "--quiet", str(wheels[0])], verbose=verbose)
        if r.returncode != 0:
            return CheckResult(
                "install_test",
                False,
                (r.stdout + r.stderr)[-600:].strip() or "pip install failed",
            )

        # 1. Import must work without minifyjs installed (it's optional)
        r = run(
            [str(python), "-c", "import teloce_npm; print(teloce_npm.__version__)"],
            verbose=verbose,
        )
        if r.returncode != 0:
            return CheckResult(
                "install_test",
                False,
                (r.stdout + r.stderr)[-600:].strip()
                or "import teloce_npm failed",
            )

        reported = r.stdout.strip()
        if reported != expected_version:
            return CheckResult(
                "install_test",
                False,
                f"installed package reports {reported!r}, expected {expected_version!r}",
            )

    return CheckResult(
        "install_test", True, f"wheel installs and imports {expected_version}"
    )


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
def run_all_checks(
    *,
    skip_tests: bool = False,
    skip_lint: bool = False,
    skip_build: bool = False,
    skip_install_test: bool = False,
    verbose: bool = False,
) -> List[CheckResult]:
    """Run every preflight check and return the collected results."""
    results: List[CheckResult] = []

    # Fast checks first — fail early before running slow ones
    results.append(check_git_repo())
    results.append(check_git_clean())
    results.append(check_branch())
    results.append(check_version_consistency())
    results.append(check_changelog_entry())
    results.append(check_pypi_availability())

    if not skip_tests:
        results.append(check_tests(verbose=verbose))

    if not skip_lint:
        results.extend(check_lint(verbose=verbose))

    if not skip_build:
        build_result = check_build(verbose=verbose)
        results.append(build_result)

        if build_result.ok:
            results.append(check_wheel_contents())
            results.append(check_twine())
            if not skip_install_test:
                results.append(check_install(verbose=verbose))

    return results


def print_report(results: List[CheckResult]) -> None:
    print()
    print(header("Preflight Report"))
    print(header("=" * 60))
    for r in results:
        print(str(r))
    print()

    passed = sum(1 for r in results if r.ok)
    failed = len(results) - passed
    if failed == 0:
        print(_c(f"ALL {passed} CHECKS PASSED ✓", "1;92"))
    else:
        print(_c(f"{passed} passed, {failed} failed", "1;91"))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="preflight",
        description="Verify the Teloce-NPM repo is ready for release.",
    )
    parser.add_argument("--skip-tests", action="store_true", help="Skip pytest.")
    parser.add_argument("--skip-lint", action="store_true", help="Skip ruff/black/mypy.")
    parser.add_argument("--skip-build", action="store_true", help="Skip build + downstream checks.")
    parser.add_argument("--skip-install-test", action="store_true", help="Skip venv install test.")
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Shorthand for --skip-tests --skip-lint --skip-install-test.",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Show subprocess output.")

    args = parser.parse_args(argv)

    skip_tests = args.skip_tests or args.fast
    skip_lint = args.skip_lint or args.fast
    skip_install = args.skip_install_test or args.fast

    results = run_all_checks(
        skip_tests=skip_tests,
        skip_lint=skip_lint,
        skip_build=args.skip_build,
        skip_install_test=skip_install,
        verbose=args.verbose,
    )
    print_report(results)
    return 0 if all(r.ok for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())