# RootTrace Codex Working Rules

## Project Context
- This project implements the "RootTrace" genealogy management system described in `docs/实验内容.md`.
- Treat `docs/实验内容.md` as the primary source of requirements before planning implementation work.
- Do not invent project paths, APIs, configuration files, dependencies, database choices, or framework details. Search and read the repository first.

## Work Scope
- Work on one milestone at a time.
- Do not implement the entire project in a single pass.
- Keep changes small, reviewable, and aligned with the current milestone.
- Before modifying code, read the relevant existing files and understand the current structure.

## Required Flow For Every Code Change
1. Read the relevant files first.
2. Before editing, output a short plan that names the files to change and the intended steps.
3. Make only the changes needed for the current milestone.
4. Run the fastest relevant verification command after changes.
5. If verification fails, fix the failure before moving to any next step.
6. After finishing, summarize:
   - what changed
   - which files changed
   - what verification command was run
   - whether verification passed
   - the recommended next milestone

## Safety Rules
- Do not delete files unless the user explicitly allows it.
- Do not hardcode secrets, tokens, passwords, private keys, `.env` values, or credentials.
- If secrets are required, ask the user to provide them through environment variables.
- Do not add analytics, telemetry, or network calls unless explicitly requested.

## Quality Rules
- Prefer type safety and explicit error handling.
- Add or update tests when behavior changes and the project has a test setup.
- Keep comments sparse; add them only when intent is not obvious.
- Keep implementation consistent with existing project style and architecture.

## Communication
- Use Chinese for explanations by default.
- Be concise and concrete.
- For debugging, report hypotheses, experiments run, and the minimal fix.
