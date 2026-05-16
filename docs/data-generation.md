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

## 模拟登录用户

生成脚本会创建 1 个统一管理用户和 `sim_user_1` 到 `sim_user_10` 普通模拟用户。这些用户使用统一演示密码：

```text
roottrace-demo
```

统一管理用户为：

```text
sim_admin
```

所有模拟族谱均由 `sim_admin` 创建。导入数据库后，使用 `sim_admin / roottrace-demo` 登录即可查看、编辑、删除全部模拟族谱，并对任意族谱进行成员、关系、导入导出等操作。

普通模拟用户 `sim_user_1` 到 `sim_user_10` 仍可登录，但默认不拥有导入的模拟族谱。该密码只用于本地实验演示，不用于生产环境。

生成数据的族谱名、姓氏、成员名和成员简介使用中文内容，例如 `陈氏族谱 1`、`陈德明`。

## 真实感规则

模拟数据不是完全随机拼接，而是按族谱演示需要生成相对自然的结构：

- 成员姓名使用中文姓氏和常见中文名，不再使用“第 N 代成员 X”这类测试占位名。
- 代际出生年份约间隔 26 年，校验时要求父母至少比子女大 16 岁。
- 同代成员先组成夫妻关系，再由上一代夫妻分配下一代子女，避免单点轮转式亲子关系。
- 婚姻开始年份按双方成年后生成，婚姻双方年龄差控制在合理范围内。
- 死亡年份按寿命区间生成，较年轻成员允许为空，表示可能仍健在。
- 简介包含籍贯、排行、职业或迁居信息，便于演示详情页。

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
