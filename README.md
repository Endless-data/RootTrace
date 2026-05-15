# RootTrace

RootTrace is a genealogy management system project based on `docs/实验内容.md`.

The project is currently in Milestone 9: ancestor query. The app supports local user registration, login, family tree creation, collaborator access control, member management, direct relationships, dashboard stats, descendant tree preview, and ancestor lookup.

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

Follow `AGENTS.md` and `PLANS.md` before implementation. Work on one milestone at a time, and do not start Milestone 10 until Milestone 9 is complete and verified.

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

Run the app locally with a generated Flask session key:

```bash
SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')" uv run flask --app app run
```

The default `DATABASE_URL` is only a local placeholder. Real database credentials and `SECRET_KEY` values must be provided through environment variables.

## Database Design

- Design document: `docs/database-design.md`
- Mermaid ER source: `docs/er.mmd`
- PostgreSQL DDL: `sql/schema.sql`
- Local PostgreSQL service: `compose.yaml`

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
