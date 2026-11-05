"""ESM wrapper: export rewriting is node-local and named exports are kept."""

import json
import subprocess
import shutil

import pytest

from teloce_npm.wrapper.esm import EsmWrapper


def _wrap(tmp_path, source):
    package_json = {"name": "pkg", "module": "index.js"}
    (tmp_path / "package.json").write_text(json.dumps(package_json), encoding="utf-8")
    (tmp_path / "index.js").write_text(source, encoding="utf-8")
    return EsmWrapper(tmp_path, "pkg", package_json).wrap()


def test_export_keyword_inside_comment_does_not_break_real_export(tmp_path):
    wrapped = _wrap(tmp_path, "// we export stuff here\nexport var create = 1;\nexport default function lib() {}\n")
    assert "export var" not in wrapped
    assert "export default" not in wrapped
    assert "we export stuff here" in wrapped  # comment untouched


def test_named_exports_are_exposed(tmp_path):
    wrapped = _wrap(tmp_path, "const a = 1; const b = 2;\nexport { a, b as bee };\nexport function f() {}\n")
    assert "__namespace['a'] = a" in wrapped
    assert "__namespace['bee'] = b" in wrapped
    assert "__namespace['f'] = f" in wrapped


def test_export_as_default_specifier(tmp_path):
    wrapped = _wrap(tmp_path, "function lib() {}\nexport { lib as default };\n")
    assert "var __default_export = lib;" in wrapped


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_wrapped_output_is_valid_javascript(tmp_path):
    wrapped = _wrap(tmp_path, "export var create = 1;\nexport default function lib() {}\n")
    out = tmp_path / "wrapped.js"
    out.write_text(wrapped, encoding="utf-8")
    assert subprocess.run(["node", "--check", str(out)], capture_output=True).returncode == 0
