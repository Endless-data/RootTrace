# RootTrace 数据导入导出流程

本文档对应实验要求中的“导入导出”：使用 PostgreSQL 的 `COPY` 命令将 CSV 数据批量导入数据库，并导出某分支的备份文件。

## RDBMS

- RDBMS：PostgreSQL
- Docker 镜像：`postgres:16-alpine`
- Compose 服务：`db`

## 准备模拟数据

先生成并验证 Milestone 12 的 CSV 数据：

```bash
uv run python scripts/generate_simulated_data.py --output data/generated --seed 20260516
uv run python scripts/validate_simulated_data.py data/generated
```

## 批量导入

启动 PostgreSQL 并加载表结构：

```bash
docker compose up -d db
docker compose exec -T db psql -U roottrace -d roottrace -f /schema/schema.sql
```

执行批量导入：

```bash
docker compose exec -T db psql -U roottrace -d roottrace -f /schema/import_simulated_data.sql
```

验证成员数量：

```bash
docker compose exec -T db psql -U roottrace -d roottrace -c "SELECT COUNT(*) FROM members;"
```

预期结果为 `100000`。

导入 SQL 使用 `COPY ... FROM` 读取容器内的 `/generated/*.csv` 文件。`compose.yaml` 将本地 `data/generated` 目录只读挂载到容器的 `/generated`。

## 导入后的登录用户

模拟数据包含 1 个统一管理用户和 10 个普通模拟用户，统一演示密码为：

```text
roottrace-demo
```

| 用户名 | 可见族谱 |
| --- | --- |
| `sim_admin` | 全部模拟族谱 |
| `sim_user_1` 到 `sim_user_10` | 默认不拥有导入的模拟族谱 |

启动 Flask 后，可以访问 `/auth/login`，使用 `sim_admin / roottrace-demo` 登录查看和管理全部模拟族谱。普通模拟用户仍可登录，用于演示普通账号，但不会默认看到批量导入的模拟族谱。

## 分支导出

默认导出根成员 ID 为 `1` 的直系后代分支：

```bash
docker compose exec -T db psql -U roottrace -d roottrace -f /schema/export_branch.sql
```

导出文件位置：

```text
exports/branch_export.csv
```

`sql/export_branch.sql` 使用 Recursive CTE 找出根成员及其所有直系后代，然后使用 `COPY (...) TO` 导出 CSV。`exports/*.csv` 已被 `.gitignore` 忽略，不提交到 git。

## 自定义导出根成员

可以通过 psql 变量覆盖默认根成员：

```bash
docker compose exec -T db psql -U roottrace -d roottrace \
  -v root_member_id=2 \
  -v output_path=/exports/branch_export_member_2.csv \
  -f /schema/export_branch.sql
```

## 关闭服务

```bash
docker compose down
```

Milestone 13 只负责导入导出流程。索引设计、执行计划和性能对比留到 Milestone 14。
