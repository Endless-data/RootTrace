# RootTrace 模拟数据生成

本文档说明 Milestone 12 的模拟数据生成方案。生成脚本使用 Python 标准库实现，输出 CSV 文件，供后续 PostgreSQL `COPY` 导入流程使用。

## 实验要求对应关系

实验要求中的数据规模约束包括：

- 至少 10 个族谱。
- 至少 1 个族谱拥有 50,000 以上成员。
- 整个系统不少于 100,000 条模拟成员数据。
- 每个族谱内的成员至少与另一个成员有亲缘关系。
- 单个族谱内至少模拟出 30 代人的传承关系。

默认生成参数满足以上约束。

## 生成命令

```bash
uv run python scripts/generate_simulated_data.py --output data/generated --seed 20260516
```

输出目录为 `data/generated/`。该目录中的大规模 CSV 和 `manifest.json` 不提交到 git，需要时本地重新生成。

## 输出文件

- `users.csv`：模拟系统用户。
- `family_trees.csv`：模拟族谱。
- `members.csv`：模拟族谱成员。
- `parent_child_relationships.csv`：模拟亲子关系。
- `marriages.csv`：模拟婚姻关系。
- `manifest.json`：生成结果摘要，包括成员总数、族谱数、最大族谱成员数、最大代数和随机种子。

## 验证命令

```bash
uv run python scripts/validate_simulated_data.py data/generated
```

验证内容包括：

- CSV 文件是否存在，字段是否与当前 schema 对齐。
- 是否满足实验要求的数据规模。
- 成员引用的族谱是否存在。
- 亲子关系两端成员是否存在且属于同一族谱。
- 父母出生年份是否早于子女出生年份。
- 婚姻双方是否存在且不是同一成员。
- 每个族谱是否至少存在亲缘关系。

## 小规模测试数据

开发和单元测试可以使用小规模生成：

```bash
uv run python scripts/generate_simulated_data.py --scale test --output data/generated-test --seed 123
uv run python scripts/validate_simulated_data.py data/generated-test --allow-small
```

`--allow-small` 只跳过完整实验规模校验，仍会检查字段和引用一致性。

## 可复现性

脚本使用 `--seed` 控制随机数。相同参数和相同 seed 会生成一致的 CSV 和 `manifest.json`。

## 后续工作边界

Milestone 12 只负责生成和验证模拟数据。数据库导入导出流程、`COPY` 命令、分支备份文件以及截图留到 Milestone 13。
