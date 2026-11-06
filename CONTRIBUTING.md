# Contributing to DevTrack

Thanks for considering a contribution!

## Before you start

1. Check existing issues and pull requests to avoid duplicate work.
2. For substantial changes, open an issue first to discuss the proposed approach.
3. Keep changes focused and explain the user problem they solve.

## Development setup

```bash
python -m venv .venv
# Activate the environment, then:
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Run tests before submitting:

```bash
python -m pytest
```

## Pull request checklist

- [ ] The change has a clear purpose.
- [ ] Tests pass locally.
- [ ] New behavior has appropriate tests.
- [ ] Documentation is updated when needed.
- [ ] No secrets, access tokens, or personal data are included.
- [ ] The pull request explains what changed and why.

## Code style

- Prefer clear, descriptive names.
- Keep API responses consistent.
- Handle external API failures explicitly.
- Avoid adding dependencies unless they provide clear value.

## Reporting security issues

Please do not publish secrets or sensitive vulnerability details in a public issue. Contact the repository maintainer privately.
