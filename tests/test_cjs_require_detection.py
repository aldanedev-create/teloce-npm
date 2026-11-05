"""Regression tests: only real require() calls may be rewritten by the CJS wrapper."""

from teloce_npm.wrapper.ast_parser import extract_requires, parse_source
from teloce_npm.wrapper.cjs import CjsWrapper


def test_extract_requires_ignores_non_require_calls():
    tree = parse_source("var a = require('dep'); var b = Function('return this')(); foo('bar');")
    assert [r["source"] for r in extract_requires(tree)] == ["dep"]


def test_function_return_this_survives_wrapping(tmp_path):
    (tmp_path / "package.json").write_text('{"name": "pkg", "main": "index.js"}', encoding="utf-8")
    (tmp_path / "index.js").write_text(
        "var root = Function('return this')();\nmodule.exports = { root: root };\n",
        encoding="utf-8",
    )
    wrapped = CjsWrapper(tmp_path, "pkg", {"name": "pkg", "main": "index.js"}).wrap()
    assert "Function('return this')()" in wrapped
    assert "window.return" not in wrapped
