"""
Consumer-side contract tests for the generated manifest.json.

Scope: verifies the manifest provides everything loader.js needs to
load packages at runtime. Distinct from tests/generator/test_manifest.py
which verifies the generator function output formatting.
"""

import json

from teloce_npm.generator.manifest import generate_manifest


def _pkg(name, version="1.0.0", size=100, deps=None):
    return {
        "name": name,
        "version": version,
        "file": f"{name}.js",
        "size": size,
        "integrity": f"sha512-{name}",
        "dependencies": deps or {},
    }


def test_manifest_is_valid_json():
    """The generated manifest must be parseable JSON."""
    parsed = json.loads(generate_manifest([_pkg("lodash")]))
    assert isinstance(parsed, dict)


def test_manifest_has_version():
    """The manifest declares its own format version."""
    parsed = json.loads(generate_manifest([]))
    assert "manifest_version" in parsed


def test_manifest_has_packages_dict():
    """The manifest must have a `packages` map keyed by package name."""
    parsed = json.loads(generate_manifest([_pkg("lodash")]))
    assert isinstance(parsed["packages"], dict)


def test_each_package_has_file_field():
    """loader.js imports `<file>` — this must be present per package."""
    parsed = json.loads(generate_manifest([_pkg("lodash")]))
    assert "file" in parsed["packages"]["lodash"]
    assert parsed["packages"]["lodash"]["file"] == "lodash.js"


def test_each_package_has_dependencies_field():
    """loader.js reads `<dependencies>` to order loading."""
    parsed = json.loads(generate_manifest([_pkg("lodash")]))
    assert "dependencies" in parsed["packages"]["lodash"]
    assert isinstance(parsed["packages"]["lodash"]["dependencies"], dict)


def test_dependency_chain_preserved():
    """A package's dependencies must be preserved for ordering."""
    packages = [_pkg("chart.js", deps={"dayjs": "^1.11.0"})]
    parsed = json.loads(generate_manifest(packages))
    assert parsed["packages"]["chart.js"]["dependencies"] == {"dayjs": "^1.11.0"}


def test_base_path_present():
    """The manifest declares the URL prefix that loader.js prepends."""
    parsed = json.loads(generate_manifest([_pkg("lodash")]))
    assert "base_path" in parsed
    assert parsed["base_path"].startswith("/")


def test_loader_can_compute_url_for_each_package():
    """
    Verify that base_path + file produces a valid URL for loader.js
    to import. E.g., '/static/teloce-npm' + '/lodash.js'.
    """
    parsed = json.loads(generate_manifest([_pkg("lodash")]))
    pkg = parsed["packages"]["lodash"]
    url = parsed["base_path"].rstrip("/") + "/" + pkg["file"]
    assert url == "/static/teloce-npm/lodash.js"


def test_total_size_is_sum_of_packages():
    """Sanity: total_size matches the sum of individual sizes."""
    packages = [_pkg("a", size=100), _pkg("b", size=250)]
    parsed = json.loads(generate_manifest(packages))
    assert parsed["total_size"] == 350
