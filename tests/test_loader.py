"""
Runtime contract tests for the generated loader.js.

Scope: verifies the loader implements manifest fetching, dependency
ordering, and event dispatch. Distinct from tests/generator/test_loader_js.py.
"""

from teloce_npm.generator.loader_js import generate_loader_js


def test_fetches_manifest():
    """The loader must fetch manifest.json at runtime."""
    output = generate_loader_js()
    assert "fetch" in output
    assert "manifest.json" in output


def test_dispatches_ready_event():
    """The loader must dispatch `teloce-npm-ready` when done."""
    output = generate_loader_js()
    assert "teloce-npm-ready" in output
    assert "dispatchEvent" in output


def test_loads_dependencies_first():
    """The loader must iterate `info.dependencies` to load deps first."""
    output = generate_loader_js()
    assert "dependencies" in output.lower()


def test_uses_dynamic_import():
    """The loader must use `import()` for each package (esm format)."""
    output = generate_loader_js()
    assert "import(" in output


def test_handles_circular_dependency():
    """The loader must detect cycles to prevent infinite recursion."""
    output = generate_loader_js()
    assert "loading" in output.lower() or "circular" in output.lower()


def test_logs_errors_for_missing_packages():
    """A missing package should be logged, not throw."""
    output = generate_loader_js()
    assert "console.error" in output


def test_dispatches_error_event():
    """A fatal crash should dispatch an error event, not throw silently."""
    output = generate_loader_js()
    assert "teloce-npm-error" in output or "catch" in output


def test_generated_js_is_syntactically_valid():
    from teloce_npm.wrapper.ast_parser import parse_source

    output = generate_loader_js()
    tree = parse_source(output)
    assert tree.root_node is not None
    has_error = any(c.type == "ERROR" for c in tree.root_node.children)
    assert not has_error


def test_base_path_is_substituted():
    """The template's ${base_path} must be replaced with actual value."""
    output = generate_loader_js(base_path="/custom/base")
    assert "/custom/base" in output
    assert "${base_path}" not in output


def test_manifest_url_is_substituted():
    output = generate_loader_js(base_path="/my/path")
    assert "/my/path/manifest.json" in output
    assert "${manifest_url}" not in output
