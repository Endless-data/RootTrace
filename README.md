# RootTrace

RootTrace is a genealogy management system project based on `docs/实验内容.md`.

The project is currently in Milestone 2: project skeleton. The Flask application skeleton exists, but no genealogy business code has been implemented yet.

## Technical Baseline

- Application framework: Flask
- Programming language: Python
- Database: PostgreSQL
- Database access: SQLAlchemy
- UI approach: Flask server-rendered HTML templates
- Test framework: pytest
- Data generation: Python scripts
- Report format: Markdown first

## Current Development Rule

Follow `AGENTS.md` and `PLANS.md` before implementation. Work on one milestone at a time, and do not start Milestone 3 until Milestone 2 is complete and verified.

## Verification

Install dependencies and verify the current skeleton with:

```bash
uv sync --dev
uv run pytest
uv run flask --app app routes
```

The default `DATABASE_URL` is only a local placeholder. Real database credentials must be provided through environment variables when database milestones start.
