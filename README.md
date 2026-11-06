# DevTrack

**A lightweight open-source dashboard for exploring public GitHub repository activity.**

DevTrack turns GitHub's public repository data into a clean dashboard with repository metrics, recent commits, pull requests, issues, contributors, and locally stored metric snapshots.

## Features

- **Repository overview:** stars, forks, open issues, watchers, language, license, topics, and timestamps.
- **Activity feed:** recent commits, pull requests, and issues.
- **Contributor view:** leading contributors and contribution counts.
- **Snapshot history:** saves a local snapshot each time a repository is inspected.
- **CSV export:** export saved snapshots for further analysis.
- **API documentation:** interactive OpenAPI docs at `/docs`.
- **No frontend build step:** FastAPI serves a responsive HTML/CSS/JavaScript dashboard.
- **Optional GitHub token:** use an environment variable to increase the public API rate limit.

## Quick start

### Requirements

- Python 3.10+
- Internet connection (to access GitHub's public API)

### 1. Clone the repository

```bash
git clone https://github.com/garvagrawa1/DevTrack.git
cd devtrack
```

### 2. Create and activate a virtual environment

**Windows PowerShell**
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Start the application

```bash
uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000** in your browser.

Try `fastapi/fastapi`, `pallets/flask`, or any public GitHub repository in `owner/name` format.

## Optional: configure a GitHub token

Unauthenticated GitHub API requests have a lower rate limit. A personal access token can raise that limit.

1. Create a fine-grained token in GitHub settings.
2. For public repository read-only requests, do not grant unnecessary permissions.
3. Copy `.env.example` to `.env` and set `GITHUB_TOKEN=your_token`.
4. Load the environment variable before starting the app.

**Never commit `.env` or paste your token into source code.** The `.gitignore` file excludes `.env`.

## Run tests

```bash
python -m pytest
```

## Docker

```bash
docker build -t devtrack .
docker run --rm -p 8000:8000 devtrack
```

Then visit http://127.0.0.1:8000.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/repository/{owner}/{repo}` | Repository summary |
| GET | `/api/repository/{owner}/{repo}/activity` | Commits, PRs, issues, contributors |
| GET | `/api/history/{owner}/{repo}` | Saved local snapshots |
| GET | `/api/export/{owner}/{repo}` | Download snapshot history as CSV |
| GET | `/docs` | Interactive API docs |

## Project structure

```text
devtrack/
├── app/
│   ├── __init__.py
│   ├── main.py
│   └── static/
│       ├── index.html
│       ├── styles.css
│       └── app.js
├── tests/
│   └── test_api.py
├── .github/
│   └── workflows/
│       └── tests.yml
├── .env.example
├── .gitignore
├── Dockerfile
├── LICENSE
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
└── requirements.txt
```

## Data, privacy, and limitations

- DevTrack requests public repository data from the GitHub REST API.
- Repository snapshots are stored locally in SQLite on the machine running DevTrack.
- The app does not collect analytics or send repository data to a DevTrack server.
- GitHub API rate limits apply. Use an optional token if you need a higher limit.
- The dashboard shows a recent sample of activity, not a complete repository history.
- Snapshot history begins only after you inspect a repository using this app.

## Roadmap

- [ ] Add charts for snapshot trends.
- [ ] Add date-range filtering.
- [ ] Add repository comparison.
- [ ] Add GitHub App authentication for teams.
- [ ] Add scheduled snapshot collection.
- [ ] Add accessibility and localization improvements.

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
