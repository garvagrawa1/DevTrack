# Architecture

DevTrack is intentionally small and easy to self-host.

```text
Browser
  |
  | HTML / CSS / JavaScript
  v
FastAPI application
  |                 |
  |                 +--> GitHub REST API (public repository data)
  |
  +--> SQLite (local metric snapshots)
```

The browser calls the FastAPI endpoints. The backend calls GitHub's REST API and normalizes the response before returning it. Each repository overview lookup stores a timestamped metric snapshot in a local SQLite database. The CSV endpoint exports those locally collected snapshots.

## Trust boundaries

- GitHub responses are external input and are rendered with DOM text APIs.
- GitHub credentials are read only from the server environment.
- The SQLite database is local to the deployment.
- No user accounts or write access to GitHub are implemented.
