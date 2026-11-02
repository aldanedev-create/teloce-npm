"""
Teloce-NPM: Use npm packages in .vel files without Node.js or node_modules.

Teloce-NPM is a Python library that bridges the npm ecosystem and Python developers.
It downloads, verifies, wraps, and injects npm packages into your Teloce-Py project.

Example:
    >>> from teloce_npm import install
    >>> install()
"""

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


def install(**kwargs):
    """
    Install all packages declared in Use declarations.

    This is the primary build command. It scans .vel and .html files for
    Use <package> from teloce-npm declarations, downloads missing packages,
    verifies their security, wraps them for the browser, and injects the
    necessary <script> tags into the configured entry_html file.

    Args:
        **kwargs: Additional options passed to the InstallCommand.
                  See teloce_npm.commands.install.InstallCommand for details.

    Returns:
        None
    """
    from .commands.install import InstallCommand

    return InstallCommand().execute(**kwargs)


def add(package: str, **kwargs):
    """
    Add a single package to the project.

    Args:
        package: Package name (e.g., "lodash", "lodash@4.17.21", "lodash@^4.0.0").
        **kwargs: Additional options passed to the AddCommand.

    Returns:
        None
    """
    from .commands.add import AddCommand

    return AddCommand().execute(package, **kwargs)


def remove(package: str, **kwargs):
    """
    Remove a package from the project.

    Args:
        package: Package name to remove.
        **kwargs: Additional options passed to the RemoveCommand.

    Returns:
        None
    """
    from .commands.remove import RemoveCommand

    return RemoveCommand().execute(package, **kwargs)


def update(package: Optional[str] = None, **kwargs):
    """
    Update packages to their latest allowed versions.

    Args:
        package: Optional package name to update. If None, updates all packages.
        **kwargs: Additional options passed to the UpdateCommand.

    Returns:
        None
    """
    from .commands.update import UpdateCommand

    return UpdateCommand().execute(package, **kwargs)


def clean(**kwargs):
    """
    Clear the cache and remove all generated files.

    Args:
        **kwargs: Additional options passed to the CleanCommand.

    Returns:
        None
    """
    from .commands.clean import CleanCommand

    return CleanCommand().execute(**kwargs)


def doctor(**kwargs):
    """
    Diagnose configuration and security issues.

    Args:
        **kwargs: Additional options passed to the DoctorCommand.

    Returns:
        None
    """
    from .commands.doctor import DoctorCommand

    return DoctorCommand().execute(**kwargs)
