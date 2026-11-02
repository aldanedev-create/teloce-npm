"""
Tests for teloce_npm.commands.search.SearchCommand.

Scope: HTTP query + output formatting. HTTP mocked.
"""

from unittest.mock import MagicMock, patch

from teloce_npm.commands.search import SearchCommand


def _mock_response(data, status=200):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = data
    if status >= 400:
        from requests.exceptions import HTTPError

        resp.raise_for_status.side_effect = HTTPError()
    return resp


def _setup_project(tmp_path):
    (tmp_path / "templates").mkdir()
    (tmp_path / "templates" / "index.html").write_text("<html></html>")
    (tmp_path / "teloce-npm.json").write_text("{}", encoding="utf-8")
    return tmp_path


def test_search_prints_results(tmp_path, capsys):
    root = _setup_project(tmp_path)
    fake_data = {
        "objects": [
            {"package": {"name": "chart.js", "version": "4.4.0", "description": "Charts"}},
            {"package": {"name": "echarts", "version": "5.4.3", "description": "Apache ECharts"}},
        ]
    }

    with patch(
        "teloce_npm.commands.search.requests.get",
        return_value=_mock_response(fake_data),
    ):
        result = SearchCommand(root).execute(query="chart")

    captured = capsys.readouterr()
    assert result == 0
    assert "chart.js@4.4.0" in captured.out
    assert "echarts@5.4.3" in captured.out


def test_search_no_results(tmp_path, capsys):
    root = _setup_project(tmp_path)

    with patch(
        "teloce_npm.commands.search.requests.get",
        return_value=_mock_response({"objects": []}),
    ):
        SearchCommand(root).execute(query="nonexistent")

    captured = capsys.readouterr()
    assert "No results" in captured.out


def test_search_handles_http_error(tmp_path, capsys):
    root = _setup_project(tmp_path)

    with patch(
        "teloce_npm.commands.search.requests.get",
        return_value=_mock_response({}, status=500),
    ):
        result = SearchCommand(root).execute(query="x")

    assert result == 1
