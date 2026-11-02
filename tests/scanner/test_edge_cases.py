"""
Edge case tests for the scanner.

Scope: only unusual inputs that the happy-path tests in
test_use_scanner.py and test_file_walker.py do not cover.
"""

from teloce_npm.scanner.use_scanner import scan_file


def _write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_use_in_comment_js_style_not_matched(tmp_path):
    path = tmp_path / "App.vel"
    _write(path, "// Use lodash from teloce-npm")

    assert scan_file(path) == []


def test_use_in_comment_hash_style_not_matched(tmp_path):
    path = tmp_path / "App.vel"
    _write(path, "# Use lodash from teloce-npm")

    assert scan_file(path) == []


def test_use_in_comment_html_style_not_matched(tmp_path):
    path = tmp_path / "App.vel"
    _write(path, "<!-- Use lodash from teloce-npm -->")

    assert scan_file(path) == []


def test_use_with_trailing_comment_not_matched(tmp_path):
    """The pattern requires end-of-line after 'teloce-npm'."""
    path = tmp_path / "App.vel"
    _write(path, "Use lodash from teloce-npm  # inline comment")

    assert scan_file(path) == []


def test_use_with_different_registry_not_matched(tmp_path):
    path = tmp_path / "App.vel"
    _write(path, "Use lodash from other-registry")

    assert scan_file(path) == []


def test_use_without_package_name_not_matched(tmp_path):
    path = tmp_path / "App.vel"
    _write(path, "Use from teloce-npm")

    assert scan_file(path) == []


def test_use_without_from_clause_not_matched(tmp_path):
    path = tmp_path / "App.vel"
    _write(path, "Use lodash")

    assert scan_file(path) == []


def test_use_without_space_before_from_not_matched(tmp_path):
    path = tmp_path / "App.vel"
    _write(path, "Use lodashfrom teloce-npm")

    assert scan_file(path) == []


def test_use_without_space_after_from_not_matched(tmp_path):
    path = tmp_path / "App.vel"
    _write(path, "Use lodash fromteloce-npm")

    assert scan_file(path) == []


def test_use_with_invalid_chars_in_name_not_matched(tmp_path):
    path = tmp_path / "App.vel"
    _write(path, "Use lod!ash from teloce-npm")

    assert scan_file(path) == []


def test_scan_file_handles_nonexistent_file(tmp_path):
    """Missing file should return [] rather than raising."""
    assert scan_file(tmp_path / "does-not-exist.vel") == []


def test_scan_file_handles_empty_file(tmp_path):
    path = tmp_path / "empty.vel"
    _write(path, "")

    assert scan_file(path) == []


def test_scan_file_handles_crlf_line_endings(tmp_path):
    path = tmp_path / "App.vel"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"Use lodash from teloce-npm\r\nUse dayjs from teloce-npm\r\n")

    uses = scan_file(path)
    names = {u["package"] for u in uses}

    assert names == {"lodash", "dayjs"}


def test_scan_file_multiple_uses_same_package_no_dedup(tmp_path):
    """scan_file does NOT deduplicate (only scan_project does)."""
    path = tmp_path / "App.vel"
    _write(
        path,
        "Use lodash from teloce-npm\nUse lodash from teloce-npm",
    )

    uses = scan_file(path)

    assert len(uses) == 2
    assert all(u["package"] == "lodash" for u in uses)
