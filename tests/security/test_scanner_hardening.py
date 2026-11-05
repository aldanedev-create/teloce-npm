"""Scanner hardening: no silent skips, more evasion routes covered."""

import pytest

from teloce_npm.security import SecurityPolicy, run_security_checks
from teloce_npm.security import malware_scanner


def _scan(tmp_path, source, filename="index.js", *, raw=None, policy=None):
    (tmp_path / "package.json").write_text('{"name": "pkg", "version": "1.0.0"}', encoding="utf-8")
    (tmp_path / filename).write_bytes(raw if raw is not None else source.encode("utf-8"))
    return run_security_checks(tmp_path, "pkg", policy or SecurityPolicy())


def _types(result):
    return {f["type"] for f in result["findings"]}


@pytest.mark.parametrize(
    "source,kind",
    [
        ("var f = Function('a', 'return a + 1');", "dynamic_function"),
        ("var f = new Function('a', 'return a + 1');", "dynamic_function"),
        ("var f = Function('return ' + code)();", "dynamic_function"),
        ("eval('1+1');", "eval_usage"),
        ("window.eval('1+1');", "eval_usage"),
        ("(0, eval)('1+1');", "eval_usage"),
        ("setTimeout('doEvil()', 10);", "eval_usage"),
        ("setInterval(\"doEvil()\", 10);", "eval_usage"),
        ("import fs from 'fs';", "dangerous_module"),
        ("import { exec } from 'node:child_process';", "dangerous_module"),
        ("export * from 'net';", "dangerous_module"),
        ("export { x } from 'child_process';", "dangerous_module"),
        ("import('child_process').then(m => m.exec('id'));", "dangerous_module"),
        ("var fs = require('fs');", "dangerous_module"),
    ],
)
def test_detected_patterns(tmp_path, source, kind):
    result = _scan(tmp_path, source)
    assert result["safe"] is False
    assert kind in _types(result)


@pytest.mark.parametrize(
    "source",
    [
        "var root = Function('return this')();",
        'var root = Function("return this")();',
        "var root = new Function('return this')();",
        "setTimeout(function () { work(); }, 10);",
        "setTimeout(fn, 10);",
        "import { x } from './local.js';",
        "var path = require('./path');",
        "var arr = [1, 2, 3].map(function (n) { return n * 2; });",
    ],
)
def test_benign_patterns_are_not_flagged(tmp_path, source):
    assert _scan(tmp_path, source)["safe"] is True


def test_commonjs_files_are_scanned(tmp_path):
    result = _scan(tmp_path, "eval('x');", filename="index.cjs")
    assert result["safe"] is False


def test_utf8_bom_does_not_hide_code(tmp_path):
    result = _scan(tmp_path, "", raw=b"\xef\xbb\xbf" + b"eval('x');")
    assert "eval_usage" in _types(result)


def test_invalid_utf8_bytes_do_not_hide_code(tmp_path):
    result = _scan(tmp_path, "", raw=b"var s = '\xff\xfe'; eval('x');")
    assert "eval_usage" in _types(result)


def test_oversized_file_is_reported_not_silently_skipped(tmp_path, monkeypatch):
    monkeypatch.setattr(malware_scanner, "MAX_PARSE_BYTES", 1000)
    result = _scan(tmp_path, "/*" + "x" * 2000 + "*/ eval('hidden');")
    assert result["safe"] is False
    assert "unscanned_file" in _types(result)


def test_unscanned_file_finding_can_be_allowed_per_package(tmp_path, monkeypatch):
    monkeypatch.setattr(malware_scanner, "MAX_PARSE_BYTES", 1000)
    policy = SecurityPolicy.from_config({"allow": {"pkg": ["unscanned_file"]}})
    assert _scan(tmp_path, "/*" + "x" * 2000 + "*/", policy=policy)["safe"] is True


def test_scanner_failure_blocks_instead_of_passing(tmp_path, monkeypatch):
    def boom(source):
        raise RuntimeError("parser exploded")

    monkeypatch.setattr(malware_scanner, "parse_source", boom)
    result = _scan(tmp_path, "var a = 1;")
    assert result["safe"] is False
    assert "scan_error" in _types(result)


def test_scanner_version_is_exposed_for_cache_invalidation():
    assert isinstance(malware_scanner.SCANNER_VERSION, int) and malware_scanner.SCANNER_VERSION >= 2


# ------------------------------------------------------------- CLI-only files
def _package(tmp_path, files, bin_field=None):
    import json

    manifest = {"name": "pkg", "version": "1.0.0"}
    if bin_field is not None:
        manifest["bin"] = bin_field
    (tmp_path / "package.json").write_text(json.dumps(manifest), encoding="utf-8")
    for name, source in files.items():
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source, encoding="utf-8")
    return run_security_checks(tmp_path, "pkg", SecurityPolicy())


def test_node_modules_in_bin_directory_are_not_flagged(tmp_path):
    result = _package(tmp_path, {"lib/index.js": "export const a = 1;", "bin/main.js": "import fs from 'node:fs';\nimport { spawn } from 'child_process';"})
    assert result["safe"] is True


def test_node_modules_in_declared_bin_file_are_not_flagged(tmp_path):
    result = _package(tmp_path, {"index.js": "module.exports = 1;", "cli/run.js": "require('child_process');"}, bin_field={"pkg": "cli/run.js"})
    assert result["safe"] is True


def test_other_findings_in_bin_files_still_block(tmp_path):
    result = _package(tmp_path, {"bin/main.js": "eval(process.argv[2]);"})
    assert result["safe"] is False and "eval_usage" in _types(result)


def test_node_modules_outside_bin_are_still_flagged(tmp_path):
    result = _package(tmp_path, {"lib/index.js": "import fs from 'fs';", "bin/main.js": "import fs from 'fs';"})
    assert result["safe"] is False
    assert all("bin" not in f["file"].split("/") for f in result["findings"])


def test_bin_field_cannot_point_outside_the_package(tmp_path):
    result = _package(tmp_path, {"index.js": "require('fs');"}, bin_field={"pkg": "../elsewhere.js"})
    assert result["safe"] is False


# ------------------------------------------------------------------- parallel
def test_parallel_and_serial_scans_agree(tmp_path, monkeypatch):
    files = {f"lib/f{i}.js": ("eval('x');" if i == 3 else "var a = %d;" % i) for i in range(12)}
    files["lib/big.js"] = "var s = '" + "x" * 5000 + "';"
    monkeypatch.setattr(malware_scanner, "PARALLEL_MIN_BYTES", 1)
    monkeypatch.setattr(malware_scanner, "PARALLEL_MIN_FILES", 2)
    parallel = _package(tmp_path, files)
    monkeypatch.setattr(malware_scanner, "PARALLEL_MIN_BYTES", 10**12)
    serial = _package(tmp_path, files)
    key = lambda r: sorted((f["type"], f["file"]) for f in r["findings"])  # noqa: E731
    assert key(parallel) == key(serial)
    assert "eval_usage" in _types(parallel)
