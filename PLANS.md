# RootTrace Development Roadmap

## Project Goal

Build a genealogy management system based on `docs/实验内容.md`.

The system should support multiple users, multiple family trees, member management, blood and marriage relationships, tree previews, ancestor queries, relationship path queries, large-scale simulated data, SQL query deliverables, indexing experiments, and final report materials.

## MVP Scope

- User registration and login.
- Family tree CRUD.
- Member CRUD with fuzzy name search.
- Permission rule: users can access family trees they created or were invited to edit.
- Basic dashboard with total member count and gender ratio.
- Tree preview for one branch.
- Ancestor query by member ID.
- Relationship path query between two member IDs.
- Database schema with primary keys, foreign keys, and required constraints.
- Core SQL files for required queries.
- Seed or generation workflow for demonstrable test data.
- Minimal report artifacts required by the experiment.

## Non-goals

- Do not implement the entire project in one milestone.
- Do not add mobile apps unless explicitly requested.
- Do not add analytics, telemetry, or external network calls unless explicitly requested.
- Do not optimize for production deployment before the MVP works locally.
- Do not introduce unspecified third-party services.
- Do not hardcode secrets or database credentials.

## Tech Stack

- Application framework: Flask.
- Programming language: Python.
- Database: PostgreSQL.
- ORM or database access layer: SQLAlchemy. The exact integration style, such as SQLAlchemy directly or Flask-SQLAlchemy, will be decided during the project skeleton and schema milestones.
- Frontend/UI approach: Flask server-rendered HTML templates for the MVP.
- Test framework: pytest.
- Data generation approach: Python scripts that generate reproducible CSV or SQL-compatible data.
- Report format: Markdown first, with final export format decided according to course submission requirements.

## Milestones

### Milestone 0: Project Ground Rules And Roadmap

Goal:
- Establish project working rules and a long-term roadmap.

File scope:
- `AGENTS.md`
- `PLANS.md`
- `README.md` only if the user explicitly asks for documentation updates.

Verification command:
- `test -f AGENTS.md && test -f PLANS.md`
- `sed -n '1,220p' PLANS.md`

Completion standard:
- `AGENTS.md` exists.
- `PLANS.md` exists and includes project goal, scope, milestones, verification commands, status, progress log, and open questions.
- No business code is created.

Recommended commit message:
- `docs: add project roadmap and codex rules`

### Milestone 1: Choose Technical Baseline

Goal:
- Decide the concrete application framework, database, test tool, and local run strategy.

File scope:
- `PLANS.md`
- `README.md`
- Do not create framework, dependency, database, or application skeleton files in this milestone.

Verification command:
- `test -f PLANS.md && test -f README.md`
- `rg "Flask|PostgreSQL|SQLAlchemy|pytest|Milestone 1" PLANS.md README.md`
- `git status --short`

Completion standard:
- Tech stack is documented.
- Local setup command is documented.
- No feature implementation is mixed into this milestone.
- No `app/`, `src/`, `tests/`, dependency file, database config, migration, or business code is created.

Recommended commit message:
- `docs: define technical baseline`

### Milestone 2: Project Skeleton

Goal:
- Create the minimal runnable project structure for the selected stack.

File scope:
- `app/__init__.py`
- `app/extensions.py`
- `app/routes.py`
- `tests/test_app.py`
- `pyproject.toml`
- `uv.lock`
- `.gitignore`
- `README.md`
- `PLANS.md`

Verification command:
- `uv --version`
- `uv sync --dev`
- `uv run pytest`
- `uv run flask --app app routes`
- `git status --short`

Completion standard:
- The application can start or the base test suite can run.
- No genealogy business behavior is implemented yet.
- README documents the local verification command.
- Flask application factory `create_app()` exists.
- The root route `/` returns a minimal health response.
- SQLAlchemy is initialized as an extension, but no schema, model, migration, or database connectivity verification is added.

Recommended commit message:
- `chore: scaffold application skeleton`

### Milestone 3: Database Conceptual And Logical Design

Goal:
- Define the entities, relationships, relational schema, and normalization notes required by the experiment.

File scope:
- `docs/database-design.md`
- `docs/er.mmd`
- `sql/schema.sql`
- `compose.yaml`
- `tests/test_database_design.py`
- `README.md`
- `PLANS.md`

Verification command:
- `uv run pytest`
- `docker compose up -d db`
- `docker compose exec -T db psql -U roottrace -d roottrace -f /schema/schema.sql`
- `docker compose exec -T db psql -U roottrace -d roottrace -c "\dt"`
- `rg "users|family_trees|members|parent_child_relationships|marriages" docs/database-design.md docs/er.mmd sql/schema.sql`
- `git status --short`

Completion standard:
- Entities include users, family trees, memberships/invitations, members, parent-child relationships, and marriages, unless the final design justifies a different model.
- Relationship cardinalities are documented.
- 3NF or BCNF analysis is documented.
- Primary keys, foreign keys, and CHECK constraints are specified.
- PostgreSQL DDL can be executed against the Compose database.
- No authentication, registration, SQLAlchemy model, migration, or business route is implemented.

Recommended commit message:
- `docs: add database design`

### Milestone 4: Authentication And User Registration

Goal:
- Implement local user registration and login.

File scope:
- `app/__init__.py`
- `app/auth.py`
- `app/models.py`
- `app/templates/base.html`
- `app/templates/auth/register.html`
- `app/templates/auth/login.html`
- `tests/test_auth.py`
- `README.md`
- `PLANS.md`

Verification command:
- `uv sync --dev`
- `uv run pytest`
- `uv run flask --app app routes`
- `git status --short`

Completion standard:
- A user can register.
- A user can log in.
- Invalid login attempts fail safely.
- No passwords or secrets are hardcoded.
- Passwords are stored as hashes, not plaintext.
- Users can log out.
- Session state stores the logged-in user ID.
- No family tree access model, collaborator invitation, or authorization rule is implemented.

Recommended commit message:
- `feat: add user registration and login`

### Milestone 5: Family Tree Access Model

Goal:
- Implement family tree creation and invited collaborator access rules.

File scope:
- `app/__init__.py`
- `app/models.py`
- `app/family_trees.py`
- `app/templates/base.html`
- `app/templates/family_trees/index.html`
- `app/templates/family_trees/new.html`
- `app/templates/family_trees/detail.html`
- `tests/test_family_trees.py`
- `README.md`
- `PLANS.md`

Verification command:
- `uv sync --dev`
- `uv run pytest`
- `uv run flask --app app routes`
- `git status --short`

Completion standard:
- A user can create a family tree.
- A creator can invite another user.
- A user can only view or edit trees they created or were invited to.
- Unauthorized access is rejected.
- Non-creators cannot invite collaborators.
- No member CRUD, fuzzy member search, tree preview, or relationship feature is implemented.

Recommended commit message:
- `feat: add family tree access control`

### Milestone 6: Member CRUD And Fuzzy Search

Goal:
- Implement member creation, update, delete, list, detail, and fuzzy name search within accessible family trees.

File scope:
- `app/__init__.py`
- `app/models.py`
- `app/members.py`
- `app/templates/family_trees/detail.html`
- `app/templates/members/index.html`
- `app/templates/members/new.html`
- `app/templates/members/edit.html`
- `app/templates/members/detail.html`
- `tests/test_members.py`
- `README.md`
- `PLANS.md`

Verification command:
- `uv sync --dev`
- `uv run pytest`
- `uv run flask --app app routes`
- `git status --short`

Completion standard:
- Members store name, gender, birth/death year or date, and biography.
- Search supports fuzzy name matching.
- Member operations respect family tree permissions.
- Delete behavior is explicit and does not violate project safety rules for repository files.
- Duplicate member names are disambiguated by member ID.
- No parent-child relationship, marriage relationship, tree preview, ancestor query, or relationship path query is implemented.

Recommended commit message:
- `feat: add member management`

### Milestone 7: Relationship Management

Goal:
- Implement parent-child and marriage relationship storage and validation.

File scope:
- `app/__init__.py`
- `app/models.py`
- `app/relationships.py`
- `app/templates/members/detail.html`
- `app/templates/relationships/detail.html`
- `tests/test_relationships.py`
- `README.md`
- `PLANS.md`

Verification command:
- `uv sync --dev`
- `uv run pytest`
- `uv run flask --app app routes`
- `git status --short`

Completion standard:
- Parent-child relationships can be created and queried.
- Marriage relationships can be created and queried.
- Constraints prevent invalid obvious cases where supported by the selected database.
- Parent birth year before child birth year rule is enforced or documented if database limitations require application-level validation.
- Relationships can be deleted.
- Relationship objects must belong to the same accessible family tree.
- No dashboard, tree preview, ancestor recursive query, or relationship path query is implemented.

Recommended commit message:
- `feat: add genealogy relationship management`

### Milestone 8: Dashboard And Tree Preview

Goal:
- Add dashboard statistics and a branch tree preview.

File scope:
- `app/__init__.py`
- `app/dashboard.py`
- `app/family_trees.py`
- `app/tree_preview.py`
- `app/templates/family_trees/detail.html`
- `app/templates/tree_preview/index.html`
- `tests/test_dashboard_tree_preview.py`
- `README.md`
- `PLANS.md`

Verification command:
- `uv sync --dev`
- `uv run pytest`
- `uv run flask --app app routes`
- `git status --short`

Completion standard:
- Dashboard shows total member count and gender ratio for a selected accessible family tree.
- Tree preview displays one branch as a hierarchy or indented list.
- Output remains usable for members with duplicate names by showing IDs or other disambiguating data.
- Tree preview is scoped to an accessible family tree and starts from a root member ID.
- No ancestor recursive query or relationship path query is implemented.

Recommended commit message:
- `feat: add dashboard and tree preview`

### Milestone 9: Ancestor Query

Goal:
- Implement ancestor lookup by member ID.

File scope:
- `app/__init__.py`
- `app/ancestors.py`
- `app/templates/ancestors/index.html`
- `app/templates/family_trees/detail.html`
- `app/templates/members/detail.html`
- `tests/test_ancestors.py`
- `README.md`
- `PLANS.md`

Verification command:
- `uv sync --dev`
- `uv run pytest`
- `uv run flask --app app routes`
- `git status --short`

Completion standard:
- Given a member ID, the system returns all known ancestors above the parent generation.
- The result preserves generation depth or tree order.
- The query works for unknown depth using a recursive strategy where the selected database supports it.
- Ancestor query is scoped to an accessible family tree.
- Duplicate member names are disambiguated by member ID.
- No relationship path query or SQL deliverable is implemented.

Recommended commit message:
- `feat: add ancestor query`

### Milestone 10: Relationship Path Query

Goal:
- Implement relationship path lookup between two member IDs.

File scope:
- `app/__init__.py`
- `app/relationship_paths.py`
- `app/templates/relationship_paths/index.html`
- `app/templates/family_trees/detail.html`
- `app/templates/members/detail.html`
- `tests/test_relationship_paths.py`
- `README.md`
- `PLANS.md`

Verification command:
- `uv sync --dev`
- `uv run pytest`
- `uv run flask --app app routes`
- `git status --short`

Completion standard:
- Given two member IDs, the system reports whether a relationship path exists.
- If a path exists, the system displays the chain.
- Duplicate names do not affect correctness because IDs are used.
- Path search includes parent-child and marriage relationships as bidirectional graph edges.
- Relationship path lookup is scoped to an accessible family tree.
- No SQL deliverables or Recursive CTE files are implemented.

Recommended commit message:
- `feat: add relationship path query`

### Milestone 11: Required SQL Deliverables

Goal:
- Add standalone SQL statements for the experiment's required queries.

File scope:
- `sql/queries/required_queries.sql`
- `docs/sql-queries.md`
- `tests/test_sql_deliverables.py`
- `README.md`
- `PLANS.md`

Verification command:
- `uv run pytest tests/test_sql_deliverables.py`
- `uv run pytest`
- `docker compose up -d db`
- `docker compose exec -T db psql -U roottrace -d roottrace -f /schema/schema.sql`
- `docker compose exec -T db psql -U roottrace -d roottrace -f /schema/queries/required_queries.sql`
- `git status --short`

Completion standard:
- SQL exists for spouse and children lookup.
- SQL exists for recursive ancestor lookup.
- SQL exists for generation with longest average lifespan.
- SQL exists for male members over 50 without spouse.
- SQL exists for members born earlier than their generation average.
- Each requirement is implemented with one SQL statement where required.
- SQL uses PostgreSQL syntax and can be executed by psql after loading `sql/schema.sql`.
- Documentation explains the purpose, parameters, and output fields for each query.

Recommended commit message:
- `feat: add required sql queries`

### Milestone 12: Simulated Data Generation

Goal:
- Generate demonstrable large-scale genealogy data according to the experiment constraints.

File scope:
- `scripts/generate_simulated_data.py`
- `scripts/validate_simulated_data.py`
- `tests/test_data_generation.py`
- `docs/data-generation.md`
- `data/generated/README.md`
- `.gitignore`
- `README.md`
- `PLANS.md`

Verification command:
- `uv run pytest tests/test_data_generation.py`
- `uv run pytest`
- `uv run python scripts/generate_simulated_data.py --output data/generated --seed 20260516`
- `uv run python scripts/validate_simulated_data.py data/generated`
- `git status --short`

Completion standard:
- At least 10 family trees can be generated.
- At least one family tree has more than 50,000 members.
- The system has at least 100,000 simulated members.
- Each family tree contains related members.
- At least one family tree has at least 30 generations.
- Generated outputs are documented and reproducible.
- Generated CSV and manifest outputs are ignored by git.
- The generator and validator use the current PostgreSQL schema column names.

Recommended commit message:
- `feat: add simulated genealogy data generator`

### Milestone 13: Import And Export Workflow

Goal:
- Document and verify database import/export using the selected RDBMS tooling.

File scope:
- `sql/import_simulated_data.sql`
- `sql/export_branch.sql`
- `docs/import-export.md`
- `tests/test_import_export_sql.py`
- `exports/README.md`
- `compose.yaml`
- `.gitignore`
- `README.md`
- `PLANS.md`

Verification command:
- `uv run pytest tests/test_import_export_sql.py`
- `uv run pytest`
- `uv run python scripts/generate_simulated_data.py --output data/generated --seed 20260516`
- `uv run python scripts/validate_simulated_data.py data/generated`
- `docker compose up -d db`
- `docker compose exec -T db psql -U roottrace -d roottrace -f /schema/schema.sql`
- `docker compose exec -T db psql -U roottrace -d roottrace -f /schema/import_simulated_data.sql`
- `docker compose exec -T db psql -U roottrace -d roottrace -c "SELECT COUNT(*) FROM members;"`
- `docker compose exec -T db psql -U roottrace -d roottrace -f /schema/export_branch.sql`
- `docker compose down`
- `git status --short`

Completion standard:
- Bulk import command is documented and tested.
- Branch export or backup command is documented and tested.
- RDBMS name and version are recorded.
- Imported simulated data reaches 100,000 members.
- Generated branch export files are ignored by git.

Recommended commit message:
- `docs: add import and export workflow`

### Milestone 14: Index And Performance Experiment

Goal:
- Add indexes and record performance comparison for the required query.

File scope:
- TODO: index SQL/migration files.
- TODO: performance notes path.
- TODO: EXPLAIN output artifact path.

Verification command:
- TODO: database-specific EXPLAIN command.

Completion standard:
- Index strategy covers fuzzy name search.
- Index strategy covers querying children by parent ID.
- Performance comparison is recorded with and without indexes.
- EXPLAIN output is captured and explained.

Recommended commit message:
- `perf: add indexes and performance analysis`

### Milestone 15: Final Report Assembly

Goal:
- Assemble final experiment report and submission artifacts.

File scope:
- TODO: report document path.
- TODO: diagram export path.
- TODO: SQL result screenshot path.
- TODO: database export path.

Verification command:
- TODO: report build/export command or manual checklist.

Completion standard:
- Report includes ER diagram.
- Report includes relational schema and 3NF or BCNF analysis.
- Report includes constraints and indexes.
- Report includes data generation method and source code reference.
- Report includes RDBMS name and version.
- Report includes SQL statements and execution result screenshots.
- Database export or backup file is prepared.

Recommended commit message:
- `docs: assemble final experiment report`

## Current Status

- `AGENTS.md` exists and defines project-specific Codex working rules.
- `docs/实验内容.md` exists and is the primary requirements document.
- `README.md` documents the project baseline.
- `PLANS.md` exists as the long-term roadmap.
- Milestone 1 technical baseline has been selected: Flask, Python, PostgreSQL, SQLAlchemy, server-rendered HTML templates, pytest, Python data generation scripts, and Markdown-first reporting.
- Milestone 2 Flask application skeleton has been created.
- Milestone 3 database design artifacts and PostgreSQL Compose validation environment have been created.
- Milestone 4 local user registration and login have been implemented.
- Milestone 5 family tree creation and collaborator access control have been implemented.
- Milestone 6 member CRUD and fuzzy member search have been implemented.
- Milestone 7 direct parent-child and marriage relationship management has been implemented.
- Milestone 8 dashboard statistics and descendant tree preview have been implemented.
- Milestone 9 ancestor query has been implemented.
- Milestone 10 relationship path query has been implemented.
- Milestone 11 required SQL deliverables have been implemented.
- Milestone 12 simulated data generator has been implemented.
- Milestone 13 import/export workflow has been implemented.
- No index experiment or final report has been implemented yet.

## Progress Log

- 2026-05-07: Read current repository files and experiment requirements.
- 2026-05-07: Added `AGENTS.md` for project working rules.
- 2026-05-07: Added `PLANS.md` roadmap.
- 2026-05-07: Completed Milestone 1 technical baseline documentation.
- 2026-05-08: Created Milestone 2 minimal Flask application skeleton.
- 2026-05-09: Created Milestone 3 database design, Mermaid ER source, PostgreSQL DDL, and Compose validation environment.
- 2026-05-09: Created Milestone 4 local registration, login, logout, and authentication tests.
- 2026-05-09: Created Milestone 5 family tree creation, collaborator invitation, and access-control tests.
- 2026-05-12: Created Milestone 6 member CRUD, scoped fuzzy search, and member access-control tests.
- 2026-05-12: Created Milestone 7 parent-child and marriage relationship management tests.
- 2026-05-12: Created Milestone 8 dashboard statistics and descendant tree preview tests.
- 2026-05-13: Created Milestone 9 ancestor query page and tests.
- 2026-05-15: Created Milestone 10 relationship path query page and tests.
- 2026-05-15: Created Milestone 11 required SQL queries and query documentation.
- 2026-05-16: Created Milestone 12 simulated data generator, validator, and documentation.
- 2026-05-16: Created Milestone 13 PostgreSQL import/export workflow documentation and SQL.

## Open Questions

- Should SQLAlchemy be used directly or through Flask-SQLAlchemy?
- Which Python version should be required for the project?
- Which PostgreSQL version should be documented and used for screenshots?
- Should local development use a system PostgreSQL install or Docker Compose?
- What final report export format is required by the course?
- Should generated large data files be committed, ignored, or produced on demand?
- What is the preferred language for code comments and report text?
