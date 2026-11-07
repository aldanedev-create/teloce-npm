# Python API: commands

Everything the CLI does is available from Python. The command line is a thin layer over these classes.

## Quick helpers

```python
import teloce_npm

teloce_npm.install()                          # scan and install, like `teloce-npm install`
teloce_npm.install(no_verify=False, frozen=True)
teloce_npm.add("lodash@4.17.21")
teloce_npm.remove("lodash")
teloce_npm.update()                           # or update("d3")
teloce_npm.clean()
teloce_npm.doctor()
```

| Function | Signature |
| --- | --- |
| `install` | `install(project_root=None, **kwargs)` |
| `add` | `add(package, project_root=None, **kwargs)` |
| `remove` | `remove(package, project_root=None, **kwargs)` |
| `update` | `update(package=None, project_root=None, **kwargs)` |
| `clean` | `clean(project_root=None, **kwargs)` |
| `doctor` | `doctor(project_root=None, **kwargs)` |

- `project_root` is the project folder (a `pathlib.Path`). It defaults to the current directory.
- Extra keyword arguments go to the command's `execute()`. For `install` and `add` these are `verbose`, `no_verify` and (for `install`) `frozen`.
- Every function returns the **exit code** as an `int`: `0` on success, non-zero on failure. They print progress to standard output and do not raise for ordinary failures such as a blocked package.

```python
from pathlib import Path
import teloce_npm

code = teloce_npm.install(project_root=Path("my-app"), frozen=True)
if code != 0:
    raise SystemExit(code)
```

## Command classes

Each command is a class in `teloce_npm.commands.<name>`. They all take an optional `project_root` and have an `execute()` method that returns an exit code.

```python
from pathlib import Path
from teloce_npm.commands.install import InstallCommand

command = InstallCommand(project_root=Path("my-app"))
exit_code = command.execute(packages=["lodash@4.17.21"], no_verify=False)
```

| Class | Module | `execute(...)` |
| --- | --- | --- |
| `InstallCommand` | `commands.install` | `execute(packages=None, production=False, verbose=False, no_verify=False, frozen=False) -> int` |
| `AddCommand` | `commands.add` | `execute(package, options=None, *, verbose=False, no_verify=False) -> int` |
| `RemoveCommand` | `commands.remove` | `execute(package) -> int` |
| `UpdateCommand` | `commands.update` | `execute(package=None) -> int` |
| `ListCommand` | `commands.list` | `execute() -> int` |
| `SearchCommand` | `commands.search` | `execute(query) -> int` |
| `InfoCommand` | `commands.info` | `execute(package) -> int` |
| `CleanCommand` | `commands.clean` | `execute() -> int` |
| `DoctorCommand` | `commands.doctor` | `execute() -> int` |

`packages=None` for `InstallCommand` means "scan the project". `production` is accepted and currently ignored. `AddCommand` accepts its options either as keyword arguments or as an `options` dict (`{"verbose": ..., "no_verify": ...}`).

The behaviour of each command is described in [Commands](../commands.md).

### `BaseCommand`

```text
BaseCommand(project_root: Optional[Path] = None)
```

The parent of all commands. It resolves the project folder, loads `teloce-npm.json`, and sets up the registry client, cache and lockfile. Subclass it to add your own command.

### `parse_package_spec`

```python
from teloce_npm.commands import parse_package_spec

parse_package_spec("lodash")             # ("lodash", "*")
parse_package_spec("lodash@4.17.21")     # ("lodash", "4.17.21")
parse_package_spec("@kurkle/color@^0.3") # ("@kurkle/color", "^0.3")
```

Splits `name@range` into `(name, range)`. A missing range is `"*"`. Scoped names are handled.

## Errors

All Teloce-NPM exceptions derive from `TeloceNpmError` (`teloce_npm.utils.errors`):

| Exception | Raised when |
| --- | --- |
| `ConfigError` | `teloce-npm.json` is invalid |
| `RegistryError` | The registry cannot be reached, or a download fails after retries |
| `PackageNotFoundError` | A package or version does not exist |
| `SecurityError` | A check fails: bad integrity, a disallowed URL, an invalid package name, a dangerous archive, a size limit |
| `LockfileMismatch` | The lockfile does not match what is installed |

The CLI catches these, prints `Error: <message>` to standard error and exits with `1`. When you call the classes from Python, catch `TeloceNpmError` yourself.

## The lockfile and scanner

```python
from pathlib import Path
from teloce_npm.lockfile import LockfileManager
from teloce_npm.scanner import scan_project

lock = LockfileManager(Path("my-app"))
lock.load()
print(lock.list_packages())            # {"dayjs": "1.11.23"}
print(lock.get_package_integrity("dayjs"))

print(scan_project(Path("my-app")))
# [{'package': 'lodash', 'file': 'static/js/A.vel', 'line': 1}]
```

`LockfileManager` has `load`, `save`, `exists`, `add_package`, `remove_package`, `get_package`, `get_package_version`, `get_package_integrity`, `has_package`, `list_packages`, `clear` and `summary`. `LockfileVerifier(lockfile_manager, cache_manager)` has `verify_against_cache`, `verify_versions`, `is_valid` and `report`.
