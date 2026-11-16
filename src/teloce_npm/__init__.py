"""
Teloce-NPM: Use npm packages in .vel files without Node.js or node_modules.

Teloce-NPM is a Python library that bridges the npm ecosystem and Python developers.
It downloads, verifies, wraps, and injects npm packages into your Teloce-Py project.

Example:
    >>> from teloce_npm import install
    >>> install()
"""

from pathlib import Path
from typing import Optional

from .version import __author__, __email__, __license__, __url__, __version__

# Public API exports
__all__ = [
    "__author__",
    "__email__",
    "__license__",
    "__url__",
    "__version__",
    "add",
    "clean",
    "doctor",
    "install",
    "remove",
    "update",
]


def install(project_root: Optional[Path] = None, **kwargs):
    """
    Install all packages declared in Use declarations.

    This is the primary build command. It scans .vel and .html files for
    Use <package> from teloce-npm declarations, downloads missing packages,
    verifies their security, wraps them for the browser, and injects the
    necessary <script> tags into the configured entry_html file.

    Args:
        project_root: The project directory (default: the current directory).
        **kwargs: Additional options passed to the InstallCommand.
                  See teloce_npm.commands.install.InstallCommand for details.

    Returns:
        int: The exit code (0 on success, non-zero on failure).
    """
    from .commands.install import InstallCommand

    return InstallCommand(project_root=project_root).execute(**kwargs)


def add(package: str, project_root: Optional[Path] = None, **kwargs):
    """
    Add a single package to the project.

    Args:
        package: Package name (e.g., "lodash", "lodash@4.17.21", "lodash@^4.0.0").
        project_root: The project directory (default: the current directory).
        **kwargs: Additional options passed to the AddCommand.

    Returns:
        int: The exit code (0 on success, non-zero on failure).
    """
    from .commands.add import AddCommand

    return AddCommand(project_root=project_root).execute(package, **kwargs)


def remove(package: str, project_root: Optional[Path] = None, **kwargs):
    """
    Remove a package from the project.

    Args:
        package: Package name to remove.
        project_root: The project directory (default: the current directory).
        **kwargs: Additional options passed to the RemoveCommand.

    Returns:
        int: The exit code (0 on success, non-zero on failure).
    """
    from .commands.remove import RemoveCommand

    return RemoveCommand(project_root=project_root).execute(package, **kwargs)


def update(package: Optional[str] = None, project_root: Optional[Path] = None, **kwargs):
    """
    Update packages to their latest allowed versions.

    Args:
        package: Optional package name to update. If None, updates all packages.
        project_root: The project directory (default: the current directory).
        **kwargs: Additional options passed to the UpdateCommand.

    Returns:
        int: The exit code (0 on success, non-zero on failure).
    """
    from .commands.update import UpdateCommand

    return UpdateCommand(project_root=project_root).execute(package, **kwargs)


def clean(project_root: Optional[Path] = None, **kwargs):
    """
    Clear the cache and remove all generated files.

    Args:
        project_root: The project directory (default: the current directory).
        **kwargs: Additional options passed to the CleanCommand.

    Returns:
        int: The exit code (0 on success, non-zero on failure).
    """
    from .commands.clean import CleanCommand

    return CleanCommand(project_root=project_root).execute(**kwargs)


def doctor(project_root: Optional[Path] = None, **kwargs):
    """
    Diagnose configuration and security issues.

    Args:
        project_root: The project directory (default: the current directory).
        **kwargs: Additional options passed to the DoctorCommand.

    Returns:
        int: The exit code (0 on success, non-zero on failure).
    """
    from .commands.doctor import DoctorCommand

    return DoctorCommand(project_root=project_root).execute(**kwargs)
