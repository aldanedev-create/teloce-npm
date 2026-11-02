#!/usr/bin/env python3
"""
Publish Teloce-NPM to PyPI.

Workflow:
  1. Run preflight checks (unless --skip-preflight)
  2. Build sdist + wheel
  3. twine check dist/*
  4. Confirm with user (unless --yes)
  5. twine upload dist/*
  6. git tag v<version>
  7. (optional) git push --tags

Exit codes:
  0   success
  1   preflight failed
  2   build/check failed
  3   upload failed
  4   user aborted

Usage:
    python scripts/publish.py                  # real PyPI
    python scripts/publish.py --test           # TestPyPI
    python scripts/publish.py --dry-run        # everything except upload + tag
    python scripts/publish.py --yes            # skip confirmation
    python scripts/publish.py --skip-preflight # assume preflight passed
    python scripts/publish.py --skip-tests --skip-lint  # fast path for CI
    python scripts/publish.py --push           # also push the git tag
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


# ---------------------------------------------------------------------------
# Import preflight helpers (sibling script)
# ---------------------------------------------------------------------------
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from preflight import (  # noqa: E402
    REPO_ROOT,
    DIST_DIR,
    run,
    run_all_checks,
    get_version_from_pyproject,
    print_report,
    ok,
    fail,
    warn,
    info,
    header,
    _c,
)


PYPI_REPOSITORY = "pypi"
TESTPYPI_REPOSITORY = "testpypi"
TESTPYPI_URL = "https://test.pypi.org/legacy/"


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------
def step_preflight(args) -> bool:
    print(header("\n[1/6] Preflight checks"))
    print("=" * 60)
    results = run_all_checks(
        skip_tests=args.skip_tests,
        skip_lint=args.skip_lint,
        skip_build=True,       # publish does its own build
        skip_install_test=True,  # and its own install test after build
        verbose=args.verbose,
    )
    print_report(results)
    return all(r.ok for r in results)


def step_build(args) -> Optional[Path]:
    print(header("\n[2/6] Build sdist + wheel"))
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)

    r = run([sys.executable, "-m", "build", "--sdist", "--wheel"])
    if r.returncode != 0:
        print(fail("build failed"))
        print((r.stdout + r.stderr)[-1000:])
        return None

    wheels = list(DIST_DIR.glob("*.whl"))
    sdists = list(DIST_DIR.glob("*.tar.gz"))
    if not wheels or not sdists:
        print(fail(f"missing artifacts in {DIST_DIR}"))
        return None

    print(ok(f"built {wheels[0].name}, {sdists[0].name}"))
    return wheels[0]


def step_twine_check(args) -> bool:
    print(header("\n[3/6] twine check"))
    artifacts = sorted(str(p) for p in DIST_DIR.iterdir() if p.is_file())
    r = run([sys.executable, "-m", "twine", "check", *artifacts])
    if r.returncode != 0:
        print(fail("twine check failed"))
        print((r.stdout + r.stderr)[-800:])
        return False
    print(ok("README and metadata look good"))
    return True


def step_install_test(args, wheel: Path) -> bool:
    """Quick sanity install in a temp venv."""
    print(header("\n[4/6] Install test (temp venv)"))
    import tempfile

    expected = get_version_from_pyproject()
    with tempfile.TemporaryDirectory() as tmp:
        venv = Path(tmp) / "venv"
        run([sys.executable, "-m", "venv", str(venv)])
        pip = venv / "bin" / "pip"
        python = venv / "bin" / "python"
        if sys.platform == "win32":
            pip = venv / "Scripts" / "pip.exe"
            python = venv / "Scripts" / "python.exe"

        r = run([str(pip), "install", "--quiet", str(wheel)])
        if r.returncode != 0:
            print(fail("pip install failed"))
            print((r.stdout + r.stderr)[-800:])
            return False

        r = run(
            [str(python), "-c", "import teloce_npm; print(teloce_npm.__version__)"]
        )
        if r.returncode != 0 or r.stdout.strip() != expected:
            print(fail("import sanity check failed"))
            print((r.stdout + r.stderr)[-800:])
            return False

    print(ok(f"wheel installs and imports {expected}"))
    return True


def step_confirm(version: str, test: bool) -> bool:
    target = "TestPyPI" if test else "PyPI"
    print(header(f"\n[5/6] Confirm upload to {target}"))
    print(f"  Package: {PACKAGE_NAME if 'PACKAGE_NAME' in globals() else 'teloce-npm'}")
    print(f"  Version: {version}")
    print(f"  Target:  {target}")
    answer = input(f"\n  Continue? [y/N] ").strip().lower()
    return answer in ("y", "yes")


def step_upload(version: str, test: bool) -> bool:
    print(header("\n[6/6] twine upload"))
    artifacts = sorted(str(p) for p in DIST_DIR.iterdir() if p.is_file())

    if test:
        cmd = [
            sys.executable, "-m", "twine", "upload",
            "--repository", "testpypi",
            *artifacts,
        ]
    else:
        cmd = [sys.executable, "-m", "twine", "upload", *artifacts]

    r = subprocess.run(cmd, cwd=REPO_ROOT)
    if r.returncode != 0:
        print(fail("twine upload failed"))
        return False

    target = "TestPyPI" if test else "PyPI"
    print(ok(f"uploaded {version} to {target}"))
    return True


def step_git_tag(version: str, push: bool) -> bool:
    print(header("\n[extra] Git tag"))
    tag = f"v{version}"

    existing = run(["git", "tag", "--list", tag]).stdout.strip()
    if existing:
        print(warn(f"tag {tag} already exists — skipping"))
        return True

    r = run(["git", "tag", "-a", tag, "-m", f"Release {version}"])
    if r.returncode != 0:
        print(fail(f"failed to create tag {tag}"))
        print((r.stdout + r.stderr)[-500:])
        return False
    print(ok(f"created tag {tag}"))

    if push:
        r = run(["git", "push", "origin", tag])
        if r.returncode != 0:
            print(fail(f"failed to push tag {tag}"))
            print((r.stdout + r.stderr)[-500:])
            return False
        print(ok(f"pushed {tag} to origin"))

    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="publish",
        description="Publish Teloce-NPM to PyPI (or TestPyPI).",
    )
    parser.add_argument("--test", action="store_true", help="Upload to TestPyPI.")
    parser.add_argument("--dry-run", action="store_true", help="Do everything except upload and tag.")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt.")
    parser.add_argument("--skip-preflight", action="store_true", help="Assume preflight already passed.")
    parser.add_argument("--skip-tests", action="store_true", help="Skip pytest in preflight.")
    parser.add_argument("--skip-lint", action="store_true", help="Skip linters in preflight.")
    parser.add_argument("--push", action="store_true", help="Also git push the tag after tagging.")
    parser.add_argument("--no-tag", action="store_true", help="Don't create a git tag.")
    parser.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args(argv)

    try:
        version = get_version_from_pyproject()
    except Exception as e:
        print(fail(f"could not determine version: {e}"))
        return 2

    target = "TestPyPI" if args.test else "PyPI"
    print(_c(f"Teloce-NPM {version} → {target}", "1;36"))
    print(_c("=" * 60, "1;36"))

    # 1. Preflight
    if not args.skip_preflight:
        if not step_preflight(args):
            print(fail("\npreflight failed — aborting"))
            return 1
    else:
        print(warn("skipping preflight (--skip-preflight)"))

    # 2. Build
    wheel = step_build(args)
    if wheel is None:
        return 2

    # 3. twine check
    if not step_twine_check(args):
        return 2

    # 4. Install test
    if not step_install_test(args, wheel):
        return 2

    # Dry-run: stop here
    if args.dry_run:
        print(_c("\n[dry-run] skipping upload and tag", "93"))
        return 0

    # 5. Confirm
    if not args.yes:
        if not step_confirm(version, args.test):
            print(warn("\naborted by user"))
            return 4

    # 6. Upload
    if not step_upload(version, args.test):
        return 3

    # Extra: git tag
    if not args.no_tag:
        if not step_git_tag(version, push=args.push):
            print(warn("upload succeeded, but tagging failed — tag manually"))
            # Upload is the primary success; return 0 with warning
            return 0

    print(_c(f"\n{version} published successfully to {target}.", "1;92"))
    if not args.test and not args.no_tag:
        print(info("Consider adding a GitHub release with the same tag."))
    return 0


if __name__ == "__main__":
    sys.exit(main())