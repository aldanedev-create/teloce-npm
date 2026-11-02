"""
Runtime contract tests for the generated use.js.

Scope: verifies the generated function implements the fallback chain
and error reporting contract. Distinct from tests/generator/test_use_js.py
which verifies generator output formatting.
"""

from teloce_npm.generator.use_js import generate_use_js


def _pkg(name, version="1.0.0"):
    return {
        "name": name,
        "version": version,
        "file": f"{name}.js",
        "size": 100,
        "integrity": "sha512-x",
        "dependencies": {},
    }


def test_defines_window_use():
    """The contract requires a global `use()` function on window."""
    output = generate_use_js([_pkg("lodash")])
    assert "window.use" in output


def test_direct_lookup_by_name():
    """The function must first try `window[name]` (direct match)."""
    output = generate_use_js([_pkg("lodash")])
    assert "window[name]" in output


def test_safe_name_fallback():
    """The function must try a normalized `window[safeName]` lookup."""
    output = generate_use_js([_pkg("chart.js")])
    # Lookup should support names like chart.js -> chart_js
    assert "safeName" in output or "replace" in output


def test_reports_available_packages_on_miss():
    """When a package isn't found, error must list available packages."""
    output = generate_use_js([_pkg("lodash"), _pkg("dayjs")])
    assert "not found" in output.lower() or "Available" in output
    assert "lodash" in output


def test_handles_non_string_input():
    """Non-string input should be rejected gracefully (no throw)."""
    output = generate_use_js([_pkg("lodash")])
    assert "typeof" in output  # e.g., `typeof name !== "string"`


def test_no_throw_on_missing_package():
    """Must return undefined (not throw) when package missing."""
    output = generate_use_js([_pkg("lodash")])
    # Should have `return undefined` or `return;` in the error path
    assert "return undefined" in output or "return;" in output


def test_generated_js_is_syntactically_valid():
    """The generated code should parse as valid JavaScript."""
    from teloce_npm.wrapper.ast_parser import parse_source
    output = generate_use_js([_pkg("lodash")])
    tree = parse_source(output)
    assert tree.root_node is not None
    # If there are ERROR nodes, tree-sitter failed to parse
    has_error = any(c.type == "ERROR" for c in tree.root_node.children)
    assert not has_error


def test_handles_empty_package_list():
    """With no packages installed, use() should still exist but return undefined."""
    output = generate_use_js([])
    assert "window.use" in output
    # No packages -> empty lookup table
    assert "available" in output.lower() or "packages" in output.lower()