# Cache

Teloce-NPM keeps downloads and results in `.teloce-npm/cache/` (the `cache_dir` option). The cache makes repeat installs fast and lets a build run without the registry once everything has been downloaded. It is safe to delete. **Do not commit it.**

## Layout

```
.teloce-npm/cache/
  dayjs@1.11.23/
    package.tgz        the verified download
    extracted/         the unpacked package
    wrapped.js         the generated browser file
    metadata.json
```

Scoped names are stored with `/` as `__` and `@` as `_at_`, for example `_at_kurkle__color@0.3.4`.

`metadata.json`:

```json
{
  "integrity": "sha512-...",
  "tarball_url": "https://registry.npmjs.org/dayjs/-/dayjs-1.11.23.tgz",
  "scan_result": "clean",
  "verified": true,
  "scanner_version": 2,
  "cached_at": "2026-11-06T22:25:52.324649+00:00",
  "name": "dayjs",
  "version": "1.11.23"
}
```

## When a cached package is reused

A cached package is reused only if **all** of these hold:

- the cached tarball still matches the expected SHA-512 integrity;
- it was scanned (`verified: true`) by the **current** scanner (`scanner_version`), unless the run uses `--no-verify`.

Otherwise it is downloaded or scanned again and you see `[RESCAN]`. This means a package installed once with `--no-verify` is never trusted by a later normal install, and a newer scanner automatically re-checks everything.

## Clearing it

```bash
teloce-npm clean      # cache, output, lockfile, manifest and injected tags
rm -rf .teloce-npm    # only the cache
```

Dependencies fetched during bundling are stored in the cache as tarballs; their unpacked code is temporary.
