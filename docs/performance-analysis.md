# RootTrace 索引与性能实验

本文档对应 Milestone 14，用于记录 PostgreSQL 索引设计和性能对比。实验目标是说明索引如何优化族谱系统中的常见查询，而不是修改 Flask 业务逻辑。

## 实验环境

- RDBMS：PostgreSQL
- Docker 镜像：`postgres:16-alpine`
- Compose 服务：`db`
- 数据集：`scripts/generate_simulated_data.py` 默认规模，至少 10 个族谱、100,000 名成员。
- 性能脚本：`sql/performance_experiment.sql`
- 索引脚本：`sql/indexes.sql`

实际耗时会受到本机 CPU、磁盘、Docker 资源和数据库缓存影响，因此报告中应记录本机实测结果。

## 索引策略

| 查询场景 | 索引 | 设计目的 |
| --- | --- | --- |
| 成员姓名模糊搜索 | `idx_members_name_trgm` | 使用 `pg_trgm` 的 GIN 索引支持 `ILIKE '%keyword%'`。 |
| 按族谱过滤成员 | `idx_members_family_tree` | 加速成员列表、统计和导出中的族谱范围过滤。 |
| 按族谱与辈分统计 | `idx_members_family_tree_generation` | 加速同辈平均寿命、平均出生年份等分组查询。 |
| 按父成员查询子女 | `idx_parent_child_family_tree_parent` | 加速子女列表和后代树预览。 |
| 按子成员查询父母 | `idx_parent_child_family_tree_child` | 加速祖先查询和 Recursive CTE 的递归连接。 |
| 按成员查询配偶 | `idx_marriages_family_tree_person_a`、`idx_marriages_family_tree_person_b` | 加速婚姻关系查询和亲缘路径查询。 |

`pg_trgm` 是 PostgreSQL 扩展，适合包含式模糊匹配。B-tree 索引用于外键过滤、等值查询和递归查询连接。

## 执行步骤

准备数据：

```bash
uv run python scripts/generate_simulated_data.py --output data/generated --seed 20260516
uv run python scripts/validate_simulated_data.py data/generated
docker compose up -d db
docker compose exec -T db psql -U roottrace -d roottrace -f /schema/schema.sql
docker compose exec -T db psql -U roottrace -d roottrace -f /schema/import_simulated_data.sql
```

建索引前执行性能脚本：

```bash
docker compose exec -T db psql -U roottrace -d roottrace -f /schema/performance_experiment.sql
```

创建索引：

```bash
docker compose exec -T db psql -U roottrace -d roottrace -f /schema/indexes.sql
```

建索引后再次执行性能脚本：

```bash
docker compose exec -T db psql -U roottrace -d roottrace -f /schema/performance_experiment.sql
```

实验结束后关闭服务：

```bash
docker compose down
```

## 对比记录

以下结果来自本机 Docker Compose 环境，数据规模为 100,000 名成员、96,659 条亲子关系和 4,920 条婚姻关系。单位使用 `Execution Time` 的毫秒值。

| 查询场景 | 建索引前耗时 | 建索引前计划摘要 | 建索引后耗时 | 建索引后计划摘要 | 结论 |
| --- | --- | --- | --- | --- | --- |
| 成员姓名模糊搜索 | 31.146 ms | `Seq Scan on members`，过滤 100,000 行。 | 0.346 ms | `Bitmap Index Scan on idx_members_name_trgm`。 | GIN trigram 索引显著减少全表扫描成本。 |
| 按父成员查询子女 | 0.069 ms | 使用唯一约束索引按 `parent_id` 过滤。 | 0.041 ms | 使用索引扫描后连接成员主键。 | 该查询原本已有唯一约束辅助，新索引带来小幅改善。 |
| 递归祖先查询 | 190.565 ms | 递归步骤反复 `Seq Scan on parent_child_relationships`。 | 0.585 ms | 递归步骤使用 `idx_parent_child_family_tree_child`。 | `child_id` 方向复合索引对 Recursive CTE 提升最明显。 |
| 按成员查询配偶 | 0.414 ms | `Seq Scan on marriages` 后过滤成员。 | 0.201 ms | 使用婚姻关系索引缩小族谱范围。 | 婚姻关系数据量较小，提升有限但方向正确。 |

## EXPLAIN 摘要

建索引前，成员模糊搜索的关键节点为：

```text
Seq Scan on members
Rows Removed by Filter: 100000
Execution Time: 31.146 ms
```

建索引后，成员模糊搜索的关键节点为：

```text
Bitmap Index Scan on idx_members_name_trgm
Execution Time: 0.346 ms
```

建索引前，递归祖先查询在递归阶段反复扫描亲子关系表：

```text
Seq Scan on parent_child_relationships relationship_1
Execution Time: 190.565 ms
```

建索引后，递归祖先查询命中 `family_tree_id + child_id` 复合索引：

```text
Index Scan using idx_parent_child_family_tree_child
Execution Time: 0.585 ms
```

## 结论

- 姓名模糊搜索使用 `ILIKE '%keyword%'` 时，普通 B-tree 索引无法有效支持包含式匹配，因此采用 `pg_trgm` + GIN。
- 亲子关系和婚姻关系的查询都依赖成员 ID 等值过滤，B-tree 复合索引可以降低关系表扫描成本。
- 递归祖先查询的每一步都需要从当前成员找到父母，`child_id` 方向索引对 Recursive CTE 更关键。
- 索引会增加写入和导入成本，但本系统更重视查询和演示性能，索引开销可以接受。
