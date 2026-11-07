# Lockfile

`teloce-npm.lock` records exactly what was installed so the next install, on any machine, gets the same bytes. **Commit it.**

## Format

```json
{
  "lockfile_version": "1.0.0",
  "generated_at": "2026-11-04T11:54:40.327185+00:00",
  "packages": {
    "chart.js": {
      "version": "4.6.1",
      "resolved": "https://registry.npmjs.org/chart.js/-/chart.js-4.6.1.tgz",
      "integrity": "sha512-hJyniucsFmq//EvXYvJ6c6mahPoI3kaxdjVH8awTaJ/fDNWeSqqqArixMJWkWNN6fcYvPU3HneSANFNYtRi61g==",
      "dependencies": { "@kurkle/color": "^0.3.0" },
      "wrapped": "chart_js/chart_js.js",
      "size": 207347,
      "workers": {},
      "scanned_at": "2026-11-04T11:54:40.322581+00:00",
      "scan_result": "clean"
    }
  }
}
```

| Field | Meaning |
| --- | --- |
| `version` | The exact version installed |
| `resolved` | The tarball URL it came from |
| `integrity` | SHA-512 of the tarball (SRI format). This is the trust anchor |
| `dependencies` | The package's declared dependencies |
| `wrapped` | Path of the generated file, relative to the output folder |
| `size` | Size of the generated file in bytes |
| `workers` | Worker files, by label, relative to the output folder |
| `scanned_at` | When the security scan ran |
| `scan_result` | `clean`, or `skipped` if the package was installed with `--no-verify` |

## How it is used

1. **Reproducible versions.** If a package is locked, `install` uses the locked version instead of resolving a new one.
2. **Integrity enforcement.** The registry's current integrity hash must match the locked one. If it does not, the package may have been republished or tampered with. The install is **blocked** and prints both hashes. If you trust the change, run `teloce-npm update` (or delete that entry) and review the result. Turn this off with `security.require_lockfile_match: false`.
3. **CI.** `install --frozen-lockfile` installs only what is locked and fails on anything missing or changed.

## Changing it

`install`, `remove`, `update` and `clean` rewrite the lockfile. Do not edit it by hand. Resolve merge conflicts by running `teloce-npm install` again.

`doctor` includes a lockfile verification report: it checks that every locked package is present and verified.
