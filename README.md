# RootTrace

RootTrace is a genealogy management system project based on `docs/实验内容.md`.

The project is currently in Milestone 1: technical baseline selection. No application skeleton or business code has been implemented yet.

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

Follow `AGENTS.md` and `PLANS.md` before implementation. Work on one milestone at a time, and do not start Milestone 2 until Milestone 1 is complete and verified.

## Verification

For the current milestone, verify the documentation baseline with:

```bash
test -f PLANS.md && test -f README.md
rg "Flask|PostgreSQL|SQLAlchemy|pytest|Milestone 1" PLANS.md README.md
```
