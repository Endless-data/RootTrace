# RootTrace

RootTrace is a genealogy management system project based on `docs/实验内容.md`.

The project has completed Milestone 11: required SQL deliverables. The app supports local user registration, login, family tree creation, collaborator access control, member management, direct relationships, dashboard stats, descendant tree preview, ancestor lookup, and relationship path lookup.

## Technical Baseline

- Application framework: Flask
- Programming language: Python
- Database: PostgreSQL
- Database access: SQLAlchemy
- UI approach: Flask server-rendered HTML templates
- UI foundation: local CSS in `app/static/css/app.css`
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

从示例文件创建本地环境配置：

```bash
cp .env.example .env
```

编辑 `.env`，将 `SECRET_KEY` 替换为足够长的随机值。`.env` 文件已被 git 忽略，不会提交到仓库。

Run the app locally:

```bash
docker compose up -d db
docker compose exec -T db psql -U roottrace -d roottrace -f /schema/schema.sql
uv run flask --app app run
```

The default local `DATABASE_URL` matches `compose.yaml`: `postgresql+psycopg://roottrace@localhost:5433/roottrace`.
Flask 会通过 `python-dotenv` 自动加载 `.env`。如果没有设置 `SECRET_KEY`，应用会在进程启动时生成临时开发密钥；如果希望本地会话可重复，请在 `.env` 中保留一个稳定的 `SECRET_KEY`。

## Database Design

- Design document: `docs/database-design.md`
- Mermaid ER source: `docs/er.mmd`
- PostgreSQL DDL: `sql/schema.sql`
- Required SQL queries: `sql/queries/required_queries.sql`
- SQL query explanation: `docs/sql-queries.md`
- Simulated data generation: `docs/data-generation.md`
- Import/export workflow: `docs/import-export.md`
- Local PostgreSQL service: `compose.yaml`

## Simulated Data

Generate full experiment-scale CSV data locally:

```bash
uv run python scripts/generate_simulated_data.py --output data/generated --seed 20260516
uv run python scripts/validate_simulated_data.py data/generated
```

Generated CSV files are ignored by git.

## Import And Export

Import generated CSV data into PostgreSQL and export one branch backup:

```bash
docker compose up -d db
docker compose exec -T db psql -U roottrace -d roottrace -f /schema/schema.sql
docker compose exec -T db psql -U roottrace -d roottrace -f /schema/import_simulated_data.sql
docker compose exec -T db psql -U roottrace -d roottrace -f /schema/export_branch.sql
```

The exported branch CSV is written to `exports/branch_export.csv` and ignored by git.

## Frontend

- Home page: `/`
- Shared layout: `app/templates/base.html`
- Shared stylesheet: `app/static/css/app.css`
- UI-2 improves authentication, family tree, and member management pages.
- UI-3 improves relationship management and genealogy query pages.
- Frontend demo guide: `docs/frontend-demo.md`

## 认证

- 注册：`/auth/register`
- 登录：`/auth/login`
- 退出登录：`POST /auth/logout`

## 族谱

- 查看可访问族谱：`/family-trees`
- 创建族谱：`/family-trees/new`
- 查看族谱详情：`/family-trees/<id>`
- 邀请协作者：`POST /family-trees/<id>/collaborators`

## 成员

- 查看和搜索成员：`/family-trees/<tree_id>/members`
- 创建成员：`/family-trees/<tree_id>/members/new`
- 查看成员详情：`/family-trees/<tree_id>/members/<member_id>`
- 编辑成员：`/family-trees/<tree_id>/members/<member_id>/edit`
- 删除成员：`POST /family-trees/<tree_id>/members/<member_id>/delete`

## 关系

- 管理成员关系：`/family-trees/<tree_id>/members/<member_id>/relationships`
- 添加父母：`POST /family-trees/<tree_id>/members/<member_id>/relationships/parents`
- 添加子女：`POST /family-trees/<tree_id>/members/<member_id>/relationships/children`
- 添加配偶：`POST /family-trees/<tree_id>/members/<member_id>/relationships/marriages`

## 数据概览和后代树预览

- 数据概览显示在：`/family-trees/<tree_id>`
- 后代树预览：`/family-trees/<tree_id>/tree-preview?root_member_id=<member_id>`

## 祖先查询

- 祖先查询：`/family-trees/<tree_id>/ancestors?member_id=<member_id>`

## 亲缘路径查询

- 亲缘路径查询：`/family-trees/<tree_id>/relationship-path?source_member_id=<id>&target_member_id=<id>`
