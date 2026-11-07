# Python API: security

`teloce_npm.security` holds the checks that run on every package. The [Security](../security.md) page explains what they mean; this page is for calling them yourself, for example to vet a package directory in a script.

```python
from pathlib import Path
from teloce_npm.security import SecurityPolicy, run_security_checks

policy = SecurityPolicy.from_config({"allow": {"d3": ["dynamic_function"]}})
result = run_security_checks(Path("extracted/package"), "d3", policy)

if not result["safe"]:
    for finding in result["findings"]:
        print(finding["severity"], finding["type"], finding["file"], finding["message"])
```

## `run_security_checks(package_dir, package_name, policy) -> dict`

Runs the install-script check and the code scan, then applies `policy.allow`. Returns:

| Key | Meaning |
| --- | --- |
| `safe` | `True` if no blocking (HIGH) finding remains |
| `findings` | The findings that still count |
| `allowed` | Findings removed because `policy.allow` lists their type for this package |

A finding is a dict: `type`, `severity` (`HIGH` or `MEDIUM`), `message`, and usually `file`. Only `HIGH` blocks.

Finding types: `install_script`, `dangerous_module`, `eval_usage`, `dynamic_function`, `process_env_access`, `high_entropy`, `unscanned_file`, `scan_error`.

## `SecurityPolicy`

A dataclass with the settings from the `security` block of `teloce-npm.json`. Build it from a config dict:

```python
policy = SecurityPolicy.from_config(config["security"])
```

Missing keys take their defaults. Useful fields: `scan_packages`, `block_install_scripts`, `check_osv`, `fail_on_critical`, `allow_vulnerabilities`, `require_osv`, `max_tarball_bytes`, `max_unpacked_bytes`, `max_files`, `allowed_registries`, `block_unknown_domains`, `allow`.

## Other functions

| Function | Purpose |
| --- | --- |
| `scan_package(package_dir, package_name, policy)` | Only the code scan. Scans every `.js`, `.mjs` and `.cjs` file |
| `check_install_scripts(package_dir, package_name)` | Raises if the package declares blocked install scripts |
| `check_vulnerabilities(package_name, version, *, strict=False)` | Looks the version up in OSV. Returns a list of `{id, summary, severity, affected}`. With `strict=True` it raises `RegistryError` instead of returning `[]` when OSV cannot be reached |
| `IntegrityVerifier()` | `compute(path)`, `verify_tarball(path, expected)`, `verify_bytes(data, expected)` for SHA-512 SRI hashes |

`severity` in vulnerability results is `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` or `UNKNOWN`. It is taken from the advisory's own label when it has one, and otherwise computed from its CVSS v3 vector.

## Validation helpers

`teloce_npm.security.validation` holds the checks applied to untrusted input:

```python
from teloce_npm.security.validation import validate_package_name, validate_version, validate_url

validate_package_name("@kurkle/color")     # returns the name, or raises SecurityError
validate_version("1.2.3-beta.1")
validate_url("https://registry.npmjs.org/x.tgz", ["registry.npmjs.org"], what="Tarball URL")
```

`validate_url` accepts `https` only (and `http` for loopback hosts), rejects credentials, and checks the host against the list when one is given. The match is exact, so `registry.npmjs.org.evil.com` does not pass.

## Scanner constants

`teloce_npm.security.malware_scanner` exposes `SCANNER_VERSION` (bumped whenever detection changes, which invalidates cached scan results), `MAX_PARSE_BYTES` (32 MB; larger files are reported as `unscanned_file`) and the parallelism thresholds.
