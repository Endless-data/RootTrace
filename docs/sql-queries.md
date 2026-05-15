# RootTrace SQL 核心查询说明

本文档对应实验要求中的“SQL 核心功能编写 (DML & Query)”。SQL 文件位于 `sql/queries/required_queries.sql`，目标数据库为 PostgreSQL。

SQL 文件使用 psql 变量作为输入参数：

- `:member_id`：成员 ID。
- `:family_tree_id`：族谱 ID。

文件开头提供了默认变量值，因此在空数据库中也可以直接执行，用于检查 SQL 语法。

## 查询 1：配偶及所有子女

实验要求：给定一个成员 ID，查询其配偶及所有子女。

输入参数：

- `:member_id`

输出字段：

- `relationship_kind`：关系类型，取值为 `spouse` 或 `child`。
- `related_member_id`：相关成员 ID。
- `related_member_name`：相关成员姓名。
- `related_member_gender`：相关成员性别。
- `start_year`、`end_year`：婚姻起止年份；子女关系中为 `NULL`。

## 查询 2：递归祖先查询

实验要求：使用 Recursive CTE，输入成员 A 的 ID，输出其向上追溯的所有历代祖先。

输入参数：

- `:member_id`

输出字段：

- `source_member_id`：查询起点成员 ID。
- `ancestor_member_id`：祖先成员 ID。
- `ancestor_name`：祖先姓名。
- `ancestor_gender`：祖先性别。
- `relationship_type`：父/母关系类型，取值为 `father` 或 `mother`。
- `depth`：距离起点成员的代数，父母为 1，祖父母为 2。

为避免错误数据导致无限递归，SQL 中限制最多向上追溯 100 层。

## 查询 3：平均寿命最长的一代

实验要求：统计某个家族中平均寿命最长的一代人。

输入参数：

- `:family_tree_id`

输出字段：

- `family_tree_id`：族谱 ID。
- `generation`：辈分编号。
- `average_lifespan_years`：平均寿命。
- `member_count`：参与统计的成员数量。

现有表结构只有 `birth_year` 和 `death_year`，没有完整日期。仍在世或未填写死亡年份的成员使用当前年份估算寿命；没有出生年份或没有辈分的成员不参与统计。

## 查询 4：超过 50 岁且无配偶的男性成员

实验要求：查询所有年龄超过 50 岁且没有配偶的男性成员。

输入参数：

- 无。

输出字段：

- `id`：成员 ID。
- `family_tree_id`：所属族谱 ID。
- `name`：成员姓名。
- `birth_year`：出生年份。
- `age_years`：按当前年份估算的年龄。

年龄按 `当前年份 - birth_year` 计算。没有出生年份的成员不参与查询。

## 查询 5：早于同辈平均出生年份的成员

实验要求：找出家族中出生年份早于该辈分平均出生年份的所有成员。

输入参数：

- `:family_tree_id`

输出字段：

- `id`：成员 ID。
- `family_tree_id`：所属族谱 ID。
- `name`：成员姓名。
- `generation`：辈分编号。
- `birth_year`：出生年份。
- `average_birth_year`：该辈分平均出生年份。

没有出生年份或没有辈分的成员不参与统计。

## 验证命令

```bash
uv run pytest tests/test_sql_deliverables.py
docker compose up -d db
docker compose exec -T db psql -U roottrace -d roottrace -f /schema/schema.sql
docker compose exec -T db psql -U roottrace -d roottrace -f /schema/queries/required_queries.sql
```

这些 SQL 是课程报告用的核心查询交付物，不替代当前 Flask 页面中的业务查询逻辑。
