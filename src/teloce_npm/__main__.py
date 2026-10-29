"""
CLI entry point for Teloce-NPM.

Usage:
    teloce-npm install                       # Scan .vel files, install everything
    teloce-npm install lodash                # Install lodash and add to config
    teloce-npm install lodash@4.17.21        # Install a specific version
    teloce-npm install lodash chart.js       # Install multiple packages
    teloce-npm add <package>                 # Alias for `install <package>`
    teloce-npm remove <package>
    teloce-npm update [<package>]
    teloce-npm list
    teloce-npm search <query>
    teloce-npm info <package>
    teloce-npm clean
    teloce-npm doctor
"""

import argparse
import sys

from .version import __version__


def _build_parser() -> argparse.ArgumentParser:
    """Build the argument parser (extracted so tests can call it)."""
    parser = argparse.ArgumentParser(
        prog="teloce-npm",
        description="Manage npm packages in Teloce-Py projects without Node.js.",
        epilog="For more information, visit https://github.com/aldanedev-create/teloce-npm",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show version and exit.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        description="Available commands",
        metavar="<command>",
    )

    # --- install (primary) ---
    install_parser = subparsers.add_parser(
        "install",
        help="Install packages, or scan .vel files if no packages are specified.",
        description=(
            "With no arguments: scans .vel and .html files for Use declarations "
            "and installs all missing packages (the primary build command). "
            "With package arguments: installs those specific packages and adds "
            "them to teloce-npm.json."
        ),
    )
    install_parser.add_argument(
        "packages",
        nargs="*",
        default=[],
        help=(
            "Optional package specs (e.g., lodash, lodash@4.17.21, lodash@^4.17.0). "
            "If omitted, scans .vel files for Use declarations."
        ),
    )
    install_parser.add_argument(
        "--production",
        action="store_true",
        help="Install production dependencies only.",
    )
    install_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output.",
    )
    install_parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip security checks (DANGEROUS! Use only for trusted packages).",
    )

    # --- add (alias for `install <pkg>`) ---
    add_parser = subparsers.add_parser(
        "add",
        help="Add a single package (alias for `install <package>`).",
        description="Installs a single package and registers it in teloce-npm.json.",
    )
    add_parser.add_argument(
        "package",
        help="Package name and optional version (e.g., lodash, lodash@4.17.21, lodash@^4.17.0).",
    )
    add_parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip security checks (DANGEROUS! Use only for trusted packages).",
    )
    add_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output.",
    )

    # --- remove ---
    remove_parser = subparsers.add_parser(
        "remove",
        help="Remove a package from the project.",
        description="Removes the package from cache, output, lockfile, manifest, and HTML.",
    )
    remove_parser.add_argument(
        "package",
        help="Package name to remove.",
    )

    # --- update ---
    update_parser = subparsers.add_parser(
        "update",
        help="Update packages to their latest allowed versions.",
        description=(
            "Checks for newer versions, downloads them, runs security checks, "
            "and updates outputs."
        ),
    )
    update_parser.add_argument(
        "package",
        nargs="?",
        default=None,
        help="Optional package name to update. If omitted, updates all packages.",
    )

    # --- list ---
    subparsers.add_parser(
        "list",
        help="List installed packages.",
        description="Shows all installed packages, their versions, and file sizes.",
    )

    # --- search ---
    search_parser = subparsers.add_parser(
        "search",
        help="Search the npm registry.",
        description="Searches the npm registry for packages matching the query.",
    )
    search_parser.add_argument(
        "query",
        help="Search query (e.g., chart, lodash).",
    )

    # --- info ---
    info_parser = subparsers.add_parser(
        "info",
        help="Show package details.",
        description="Displays detailed information about a package from the npm registry.",
    )
    info_parser.add_argument(
        "package",
        help="Package name.",
    )

    # --- clean ---
    subparsers.add_parser(
        "clean",
        help="Clear cache and remove all generated files.",
        description="Removes the local cache, output, lockfile, manifest, and injected HTML.",
    )

    # --- doctor ---
    subparsers.add_parser(
        "doctor",
        help="Diagnose configuration and security issues.",
        description="Checks the environment, configuration, and installed packages for common issues.",
    )

    return parser


def main() -> int:
    """
    Main CLI entry point.

    Returns:
        int: Exit code (0 for success, non-zero for failure).
    """
    parser = _build_parser()
    args = parser.parse_args()

    # If no command is provided, show help and exit
    if not args.command:
        parser.print_help()
        return 1

    # Dispatch to the appropriate command
    try:
        if args.command == "install":
            from .commands.install import InstallCommand
            return InstallCommand().execute(
                packages=args.packages,
                production=args.production,
                verbose=args.verbose,
                no_verify=args.no_verify,
            )

        elif args.command == "add":
            # `add` is an alias for `install <package>`
            from .commands.install import InstallCommand
            return InstallCommand().execute(
                packages=[args.package],
                verbose=args.verbose,
                no_verify=args.no_verify,
            )

        elif args.command == "remove":
            from .commands.remove import RemoveCommand
            return RemoveCommand().execute(package=args.package)

        elif args.command == "update":
            from .commands.update import UpdateCommand
            return UpdateCommand().execute(package=args.package)

        elif args.command == "list":
            from .commands.list import ListCommand
            return ListCommand().execute()

        elif args.command == "search":
            from .commands.search import SearchCommand
            return SearchCommand().execute(query=args.query)

        elif args.command == "info":
            from .commands.info import InfoCommand
            return InfoCommand().execute(package=args.package)

        elif args.command == "clean":
            from .commands.clean import CleanCommand
            return CleanCommand().execute()

        elif args.command == "doctor":
            from .commands.doctor import DoctorCommand
            return DoctorCommand().execute()

        else:
            parser.print_help()
            return 1

    except KeyboardInterrupt:
        print("\nAborted by user.", file=sys.stderr)
        return 130

    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())