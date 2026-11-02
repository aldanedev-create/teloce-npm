"""
Tests for teloce_npm.generator.manifest.

Scope: only manifest.json generation.
"""

import json

from teloce_npm.generator.manifest import (
    MANIFEST_VERSION,
    generate_manifest,
    write_manifest,
)


def _pkg(name, version="1.0.0", size=100, deps=None):
    return {
        "name": name,
        "version": version,
        "file": f"{name}.js",
        "size": size,
        "integrity": f"sha512-{name}",
        "dependencies": deps or {},
    }


# ---------------------------------------------------------------------------
# generate_manifest()
# ---------------------------------------------------------------------------
def test_output_is_valid_json():
    output = generate_manifest([_pkg("lodash")])
    parsed = json.loads(output)  # must not raise
    assert isinstance(parsed, dict)


def test_manifest_version_field():
    parsed = json.loads(generate_manifest([_pkg("lodash")]))
    assert parsed["manifest_version"] == MANIFEST_VERSION


def test_generated_at_present():
    parsed = json.loads(generate_manifest([_pkg("lodash")]))
    assert "generated_at" in parsed


def test_base_path_default():
    parsed = json.loads(generate_manifest([_pkg("lodash")]))
    assert parsed["base_path"] == "/static/teloce-npm"


def test_base_path_custom():
    parsed = json.loads(generate_manifest([_pkg("lodash")], base_path="/custom"))
    assert parsed["base_path"] == "/custom"


def test_packages_included():
    parsed = json.loads(generate_manifest([_pkg("lodash", "4.17.21")]))
    assert "lodash" in parsed["packages"]
    assert parsed["packages"]["lodash"]["version"] == "4.17.21"


def test_package_entry_has_required_fields():
    parsed = json.loads(generate_manifest([_pkg("lodash")]))
    entry = parsed["packages"]["lodash"]
    for key in ("version", "file", "size", "integrity", "dependencies"):
        assert key in entry


def test_total_size_sums_correctly():
    packages = [_pkg("a", size=100), _pkg("b", size=250), _pkg("c", size=50)]
    parsed = json.loads(generate_manifest(packages))
    assert parsed["total_size"] == 400


def test_total_size_zero_when_empty():
    parsed = json.loads(generate_manifest([]))
    assert parsed["total_size"] == 0
    assert parsed["packages"] == {}


def test_dependencies_preserved():
    packages = [_pkg("chart.js", deps={"dayjs": "^1.11.0"})]
    parsed = json.loads(generate_manifest(packages))
    assert parsed["packages"]["chart.js"]["dependencies"] == {"dayjs": "^1.11.0"}


def test_no_unsubstituted_template_markers():
    output = generate_manifest([_pkg("lodash")])
    assert "${" not in output


# ---------------------------------------------------------------------------
# write_manifest()
# ---------------------------------------------------------------------------
def test_write_creates_file(tmp_path):
    path = write_manifest([_pkg("lodash")], tmp_path / "out")
    assert path.exists()
    assert path.name == "manifest.json"


def test_write_content_matches_generate(tmp_path):
    packages = [_pkg("lodash")]
    path = write_manifest(packages, tmp_path / "out")
    on_disk = path.read_text(encoding="utf-8")
    assert on_disk == generate_manifest(packages)


def test_write_creates_output_dir(tmp_path):
    target = tmp_path / "deep" / "nested"
    path = write_manifest([_pkg("lodash")], target)
    assert path.exists()
