"""
Tests for teloce_npm.scanner.use_scanner.

Scope: only Use extraction.
Does NOT test directory traversal (that's test_file_walker.py).
Does NOT test malformed input (that's test_edge_cases.py).
"""

from pathlib import Path

from teloce_npm.scanner.use_scanner import scan_file, scan_project


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_scan_file_returns_empty_for_no_uses(tmp_path):
    path = tmp_path / "App.vel"
    _write(path, "<template><div></div></template>")

    assert scan_file(path) == []


def test_scan_file_finds_single_use(tmp_path):
    path = tmp_path / "App.vel"
    _write(path, "Use lodash from teloce-npm\n<template></template>")

    uses = scan_file(path)

    assert len(uses) == 1
    assert uses[0]["package"] == "lodash"
    assert uses[0]["file"] == str(path)
    assert uses[0]["line"] == 1


def test_scan_file_records_correct_line_number(tmp_path):
    path = tmp_path / "App.vel"
    _write(
        path,
        "<template></template>\n"
        "\n"
        "Use lodash from teloce-npm\n"
        "\n"
        "Use dayjs from teloce-npm\n",
    )

    uses = scan_file(path)
    line_map = {u["package"]: u["line"] for u in uses}

    assert line_map == {"lodash": 3, "dayjs": 5}


def test_scan_file_handles_scoped_package(tmp_path):
    path = tmp_path / "App.vel"
    _write(path, "Use @types/node from teloce-npm")

    uses = scan_file(path)

    assert uses[0]["package"] == "@types/node"


def test_scan_file_handles_case_insensitive(tmp_path):
    path = tmp_path / "App.vel"
    _write(path, "use lodash from teloce-npm")

    uses = scan_file(path)

    assert len(uses) == 1
    assert uses[0]["package"] == "lodash"


def test_scan_file_handles_leading_whitespace(tmp_path):
    path = tmp_path / "App.vel"
    _write(path, "    Use lodash from teloce-npm")

    uses = scan_file(path)

    assert len(uses) == 1


def test_scan_file_handles_trailing_whitespace(tmp_path):
    path = tmp_path / "App.vel"
    _write(path, "Use lodash from teloce-npm   ")

    uses = scan_file(path)

    assert len(uses) == 1


def test_scan_file_handles_dot_and_dash_in_name(tmp_path):
    path = tmp_path / "App.vel"
    _write(path, "Use chart.js from teloce-npm\nUse date-fns from teloce-npm")

    uses = scan_file(path)
    names = {u["package"] for u in uses}

    assert names == {"chart.js", "date-fns"}


def test_scan_project_finds_uses_across_files(tmp_path):
    _write(tmp_path / "A.vel", "Use lodash from teloce-npm")
    _write(tmp_path / "B.vel", "Use dayjs from teloce-npm")

    uses = scan_project(tmp_path)
    names = {u["package"] for u in uses}

    assert names == {"lodash", "dayjs"}


def test_scan_project_deduplicates_same_package_in_same_file(tmp_path):
    _write(
        tmp_path / "App.vel",
        "Use lodash from teloce-npm\nUse lodash from teloce-npm",
    )

    uses = scan_project(tmp_path)
    lodash_uses = [u for u in uses if u["package"] == "lodash"]

    assert len(lodash_uses) == 1


def test_scan_project_keeps_same_package_in_different_files(tmp_path):
    _write(tmp_path / "A.vel", "Use lodash from teloce-npm")
    _write(tmp_path / "B.vel", "Use lodash from teloce-npm")

    uses = scan_project(tmp_path)
    lodash_uses = [u for u in uses if u["package"] == "lodash"]

    assert len(lodash_uses) == 2


def test_scan_project_finds_uses_in_html(tmp_path):
    _write(tmp_path / "index.html", "Use lodash from teloce-npm")

    uses = scan_project(tmp_path)

    assert any(u["package"] == "lodash" for u in uses)
