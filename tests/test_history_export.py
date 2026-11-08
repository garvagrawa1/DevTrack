"""Tests for the snapshot history and CSV export endpoints.

The database is pointed at a per-test temporary file (pytest tmp_path)
so these tests never touch a real database, and snapshots are inserted
directly with save_snapshot() so no GitHub API calls are made.
"""

import csv
import io
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app

client = TestClient(app)

CSV_HEADER = ["repository", "stars", "forks", "open_issues", "watchers", "captured_at"]


@pytest.fixture(autouse=True)
def no_github(monkeypatch):
    """Fail loudly if a test accidentally reaches the GitHub API."""

    def _fail(*args, **kwargs):
        raise AssertionError("test attempted to call the GitHub API")

    monkeypatch.setattr(main_module, "github_get", _fail)


@pytest.fixture()
def temp_db(tmp_path, monkeypatch):
    """Point DEVTRACK_DB at a temporary file and initialise its schema."""

    db_file = tmp_path / "devtrack-test.db"
    monkeypatch.setenv("DEVTRACK_DB", str(db_file))
    main_module.DB_PATH = db_file
    main_module.init_db()
    yield db_file
    main_module.DB_PATH = main_module.APP_DIR.parent / "devtrack.db"


def _snapshot(stars, forks, issues, watchers):
    return {
        "stargazers_count": stars,
        "forks_count": forks,
        "open_issues_count": issues,
        "subscribers_count": watchers,
    }


def _assert_iso_utc(value):
    parsed = datetime.fromisoformat(value)
    assert parsed.tzinfo is not None


def test_history_returns_saved_snapshots(temp_db):
    main_module.save_snapshot("octocat/Hello-World", _snapshot(10, 2, 3, 4))
    main_module.save_snapshot("octocat/Hello-World", _snapshot(11, 3, 2, 5))
    main_module.save_snapshot("octocat/other-repo", _snapshot(99, 9, 9, 9))

    response = client.get("/api/history/octocat/Hello-World")

    assert response.status_code == 200
    body = response.json()
    assert body["repository"] == "octocat/Hello-World"
    snapshots = body["snapshots"]
    assert len(snapshots) == 2
    assert [tuple(s[k] for k in ("stars", "forks", "open_issues", "watchers")) for s in snapshots] == [
        (10, 2, 3, 4),
        (11, 3, 2, 5),
    ]
    for snapshot in snapshots:
        assert set(snapshot) == {"stars", "forks", "open_issues", "watchers", "captured_at"}
        _assert_iso_utc(snapshot["captured_at"])
    assert snapshots[0]["captured_at"] <= snapshots[1]["captured_at"]


def test_history_unknown_repo_returns_empty_list(temp_db):
    response = client.get("/api/history/octocat/never-seen")

    assert response.status_code == 200
    assert response.json() == {"repository": "octocat/never-seen", "snapshots": []}


def test_export_returns_csv_with_header_and_rows(temp_db):
    main_module.save_snapshot("octocat/Hello-World", _snapshot(10, 2, 3, 4))
    main_module.save_snapshot("octocat/Hello-World", _snapshot(11, 3, 2, 5))

    response = client.get("/api/export/octocat/Hello-World")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == 'attachment; filename="octocat-Hello-World-history.csv"'

    rows = list(csv.reader(io.StringIO(response.text)))
    assert rows[0] == CSV_HEADER
    assert len(rows) == 3
    assert [tuple(row[1:5]) for row in rows[1:]] == [("10", "2", "3", "4"), ("11", "3", "2", "5")]
    for row in rows[1:]:
        assert row[0] == "octocat/Hello-World"
        _assert_iso_utc(row[5])
    assert rows[1][5] <= rows[2][5]


def test_export_unknown_repo_returns_header_only_csv(temp_db):
    response = client.get("/api/export/octocat/never-seen")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    rows = list(csv.reader(io.StringIO(response.text)))
    assert rows == [CSV_HEADER]


def test_export_matches_history_data(temp_db):
    main_module.save_snapshot("octocat/Hello-World", _snapshot(7, 1, 0, 6))

    history = client.get("/api/history/octocat/Hello-World").json()["snapshots"]
    rows = list(csv.reader(io.StringIO(client.get("/api/export/octocat/Hello-World").text)))

    assert rows[0] == CSV_HEADER
    assert rows[1][1:5] == [str(history[0]["stars"]), str(history[0]["forks"]), str(history[0]["open_issues"]), str(history[0]["watchers"])]
    assert rows[1][5] == history[0]["captured_at"]
