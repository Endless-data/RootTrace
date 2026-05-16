# RootTrace

RootTrace is a genealogy management system project based on `docs/实验内容.md`.

The project has completed Milestone 11: required SQL deliverables. The app supports local user registration, login, family tree creation, collaborator access control, member management, direct relationships, dashboard stats, descendant tree preview, ancestor lookup, and relationship path lookup.

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

Follow `AGENTS.md` and `PLANS.md` before implementation. Work on one milestone at a time, and do not start Milestone 12 until its implementation plan is reviewed.

## Verification

Install dependencies and verify the current skeleton and database design with:

```bash
uv sync --dev
uv run pytest
uv run flask --app app routes
docker compose up -d db
docker compose exec -T db psql -U roottrace -d roottrace -f /schema/schema.sql
docker compose exec -T db psql -U roottrace -d roottrace -c "\dt"
```

Create a local environment file from the example:

```bash
cp .env.example .env
```

Edit `.env` and replace `SECRET_KEY` with a long random value. The `.env` file is ignored by git.

Run the app locally:

```bash
docker compose up -d db
docker compose exec -T db psql -U roottrace -d roottrace -f /schema/schema.sql
uv run flask --app app run
```

The default local `DATABASE_URL` matches `compose.yaml`: `postgresql+psycopg://roottrace@localhost:5433/roottrace`.
Flask loads `.env` automatically through `python-dotenv`. If `SECRET_KEY` is not set, the app still generates a temporary development key at process startup; for repeatable local sessions, keep a stable `SECRET_KEY` in `.env`.

## Database Design

- Design document: `docs/database-design.md`
- Mermaid ER source: `docs/er.mmd`
- PostgreSQL DDL: `sql/schema.sql`
- Required SQL queries: `sql/queries/required_queries.sql`
- SQL query explanation: `docs/sql-queries.md`
- Simulated data generation: `docs/data-generation.md`
- Local PostgreSQL service: `compose.yaml`

## Simulated Data

Generate full experiment-scale CSV data locally:

```bash
uv run python scripts/generate_simulated_data.py --output data/generated --seed 20260516
uv run python scripts/validate_simulated_data.py data/generated
```

Generated CSV files are ignored by git.

## Authentication

- Register: `/auth/register`
- Login: `/auth/login`
- Logout: `POST /auth/logout`

## Family Trees

- List accessible family trees: `/family-trees`
- Create a family tree: `/family-trees/new`
- View a family tree: `/family-trees/<id>`
- Invite a collaborator: `POST /family-trees/<id>/collaborators`

## Members

- List and search members: `/family-trees/<tree_id>/members`
- Create a member: `/family-trees/<tree_id>/members/new`
- View a member: `/family-trees/<tree_id>/members/<member_id>`
- Edit a member: `/family-trees/<tree_id>/members/<member_id>/edit`
- Delete a member: `POST /family-trees/<tree_id>/members/<member_id>/delete`

## Relationships

- Manage a member's relationships: `/family-trees/<tree_id>/members/<member_id>/relationships`
- Add a parent: `POST /family-trees/<tree_id>/members/<member_id>/relationships/parents`
- Add a child: `POST /family-trees/<tree_id>/members/<member_id>/relationships/children`
- Add a spouse: `POST /family-trees/<tree_id>/members/<member_id>/relationships/marriages`

## Dashboard And Tree Preview

- Dashboard stats are shown on `/family-trees/<tree_id>`
- Descendant tree preview: `/family-trees/<tree_id>/tree-preview?root_member_id=<member_id>`

## Ancestors

- Ancestor query: `/family-trees/<tree_id>/ancestors?member_id=<member_id>`

## Relationship Path

- Relationship path query: `/family-trees/<tree_id>/relationship-path?source_member_id=<id>&target_member_id=<id>`
