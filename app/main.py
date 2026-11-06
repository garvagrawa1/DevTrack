from __future__ import annotations

import csv
import io
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

APP_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("DEVTRACK_DB", APP_DIR.parent / "devtrack.db"))
GITHUB_API = "https://api.github.com"
app = FastAPI(
    title="DevTrack API",
    description="A lightweight open-source dashboard for public GitHub repository activity.",
    version="1.0.0",
)
app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")


def db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with closing(db_connect()) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                stars INTEGER NOT NULL,
                forks INTEGER NOT NULL,
                open_issues INTEGER NOT NULL,
                watchers INTEGER NOT NULL,
                captured_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_repo ON snapshots(full_name, captured_at)")
        conn.commit()


@app.on_event("startup")
def startup() -> None:
    init_db()


class RepoRequest(BaseModel):
    repository: str = Field(min_length=3, max_length=200, examples=["fastapi/fastapi"])


def github_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "DevTrack-Open-Source-Dashboard",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def validate_repo_name(name: str) -> tuple[str, str]:
    parts = name.strip().strip("/").split("/")
    if len(parts) != 2 or not all(parts):
        raise HTTPException(status_code=400, detail="Enter a repository as owner/name.")
    if any(part in {".", ".."} or " " in part for part in parts):
        raise HTTPException(status_code=400, detail="Invalid repository name.")
    return parts[0], parts[1]


async def github_get(path: str, params: dict[str, Any] | None = None) -> Any:
    timeout = httpx.Timeout(15.0, connect=5.0)
    async with httpx.AsyncClient(timeout=timeout, headers=github_headers()) as client:
        try:
            response = await client.get(f"{GITHUB_API}{path}", params=params)
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Could not reach GitHub: {exc.__class__.__name__}") from exc
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Repository not found, or it is private.")
    if response.status_code == 403:
        remaining = response.headers.get("X-RateLimit-Remaining", "unknown")
        raise HTTPException(
            status_code=429,
            detail=f"GitHub API rate limit or access restriction (remaining: {remaining}). Add a GITHUB_TOKEN for a higher limit.",
        )
    if response.status_code == 422:
        raise HTTPException(status_code=422, detail="GitHub could not process this repository request.")
    if response.is_error:
        raise HTTPException(status_code=502, detail=f"GitHub returned HTTP {response.status_code}.")
    return response.json()


def save_snapshot(repo: str, data: dict[str, Any]) -> None:
    captured = datetime.now(timezone.utc).isoformat()
    with closing(db_connect()) as conn:
        conn.execute(
            """INSERT INTO snapshots(full_name, stars, forks, open_issues, watchers, captured_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (repo, data["stargazers_count"], data["forks_count"],
             data["open_issues_count"], data["subscribers_count"], captured),
        )
        conn.commit()


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home() -> HTMLResponse:
    return HTMLResponse((APP_DIR / "static" / "index.html").read_text(encoding="utf-8"))


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "DevTrack API"}


@app.get("/api/repository/{owner}/{repo}")
async def repository_summary(owner: str, repo: str) -> dict[str, Any]:
    full_name = f"{owner}/{repo}"
    data = await github_get(f"/repos/{owner}/{repo}")
    save_snapshot(full_name, data)
    return {
        "full_name": data["full_name"],
        "description": data.get("description"),
        "html_url": data["html_url"],
        "homepage": data.get("homepage"),
        "owner": {
            "login": data["owner"]["login"],
            "avatar_url": data["owner"]["avatar_url"],
            "html_url": data["owner"]["html_url"],
        },
        "visibility": data.get("visibility", "public"),
        "language": data.get("language"),
        "license": (data.get("license") or {}).get("spdx_id"),
        "created_at": data.get("created_at"),
        "updated_at": data.get("updated_at"),
        "pushed_at": data.get("pushed_at"),
        "stars": data["stargazers_count"],
        "forks": data["forks_count"],
        "open_issues": data["open_issues_count"],
        "watchers": data["subscribers_count"],
        "default_branch": data["default_branch"],
        "topics": data.get("topics", []),
    }


@app.get("/api/repository/{owner}/{repo}/activity")
async def repository_activity(owner: str, repo: str, per_page: int = Query(10, ge=1, le=30)) -> dict[str, Any]:
    base = f"/repos/{owner}/{repo}"
    commits, pulls, issues, contributors = await __import__("asyncio").gather(
        github_get(f"{base}/commits", {"per_page": per_page}),
        github_get(f"{base}/pulls", {"state": "all", "per_page": per_page, "sort": "updated", "direction": "desc"}),
        github_get(f"{base}/issues", {"state": "all", "per_page": per_page, "sort": "updated", "direction": "desc"}),
        github_get(f"{base}/contributors", {"per_page": min(per_page, 20)}),
    )
    return {
        "commits": [
            {
                "sha": item["sha"][:7],
                "message": item["commit"]["message"].splitlines()[0],
                "author": (item.get("author") or {}).get("login") or item["commit"]["author"]["name"],
                "date": item["commit"]["author"]["date"],
                "url": item["html_url"],
            } for item in commits
        ],
        "pull_requests": [
            {"number": p["number"], "title": p["title"], "state": p["state"],
             "user": p["user"]["login"], "updated_at": p["updated_at"], "url": p["html_url"]}
            for p in pulls
        ],
        "issues": [
            {"number": i["number"], "title": i["title"], "state": i["state"],
             "user": i["user"]["login"], "updated_at": i["updated_at"], "url": i["html_url"]}
            for i in issues if "pull_request" not in i
        ],
        "contributors": [
            {"login": c["login"], "avatar_url": c["avatar_url"], "contributions": c["contributions"],
             "url": c["html_url"]} for c in contributors
        ],
    }


@app.get("/api/history/{owner}/{repo}")
async def repository_history(owner: str, repo: str) -> dict[str, Any]:
    full_name = f"{owner}/{repo}"
    with closing(db_connect()) as conn:
        rows = conn.execute(
            """SELECT stars, forks, open_issues, watchers, captured_at
               FROM snapshots WHERE full_name = ? ORDER BY captured_at ASC LIMIT 100""",
            (full_name,),
        ).fetchall()
    return {"repository": full_name, "snapshots": [dict(row) for row in rows]}


@app.get("/api/export/{owner}/{repo}")
async def export_history(owner: str, repo: str) -> Response:
    full_name = f"{owner}/{repo}"
    with closing(db_connect()) as conn:
        rows = conn.execute(
            """SELECT stars, forks, open_issues, watchers, captured_at
               FROM snapshots WHERE full_name = ? ORDER BY captured_at ASC""",
            (full_name,),
        ).fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["repository", "stars", "forks", "open_issues", "watchers", "captured_at"])
    for row in rows:
        writer.writerow([full_name, row["stars"], row["forks"], row["open_issues"], row["watchers"], row["captured_at"]])
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{owner}-{repo}-history.csv"'},
    )
