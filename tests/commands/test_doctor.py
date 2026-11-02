"""
Tests for teloce_npm.commands.doctor.DoctorCommand.

Scope: diagnostic output for `teloce-npm doctor`.
"""

import json

from teloce_npm.commands.doctor import DoctorCommand


def _setup(tmp_path):
    (tmp_path / "templates").mkdir()
    (tmp_path / "templates" / "index.html").write_text("<html></html>")
    (tmp_path / "teloce-npm.json").write_text("{}", encoding="utf-8")
    (tmp_path / "teloce-npm.lock").write_text(
        json.dumps({
            "lockfile_version": "1.0.0",
            "generated_at": "2025-01-01T00:00:00Z",
            "packages": {},
        }),
        encoding="utf-8",
    )
    return tmp_path


def test_doctor_reports_paths(tmp_path, capsys):
    root = _setup(tmp_path)

    result = DoctorCommand(root).execute()

    captured = capsys.readouterr()
    assert result == 0
    assert "Teloce-NPM Doctor" in captured.out
    assert "Entry HTML" in captured.out
    assert "Output dir" in captured.out
    assert "Cache dir" in captured.out


def test_doctor_reports_security_policy(tmp_path, capsys):
    root = _setup(tmp_path)

    DoctorCommand(root).execute()

    captured = capsys.readouterr()
    assert "verify_integrity" in captured.out
    assert "scan_malware" in captured.out


def test_doctor_reports_lockfile_status(tmp_path, capsys):
    root = _setup(tmp_path)

    DoctorCommand(root).execute()

    captured = capsys.readouterr()
    assert "Lockfile" in captured.out or "lockfile" in captured.out


def test_doctor_reports_missing_html(tmp_path, capsys):
    root = _setup(tmp_path)
    (root / "templates" / "index.html").unlink()

    DoctorCommand(root).execute()

    captured = capsys.readouterr()
    assert "Exists:" in captured.out  # prints exists=false