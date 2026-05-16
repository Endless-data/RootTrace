# RootTrace 前端演示路径

本文档用于课程演示时快速走通 RootTrace 的主要前端页面。演示前请先确认已完成依赖安装和数据库启动。

## 1. 启动项目

在项目根目录运行：

```bash
docker compose up -d db
docker compose exec -T db psql -U roottrace -d roottrace -f /schema/schema.sql
uv run flask --app app run
```

浏览器打开：

```text
http://127.0.0.1:5000/
```

## 2. 注册和登录

1. 打开首页 `/`。
2. 点击 `Create account`。
3. 注册一个本地用户，例如：
   - Username: `alice`
   - Display name: `Alice`
   - Password: `secret`
4. 注册后进入登录状态。

如果已经注册过，可以直接访问 `/auth/login` 登录。

## 3. 创建族谱

1. 进入 `/family-trees`。
2. 点击 `Create family tree`。
3. 示例数据：
   - Name: `Chen Genealogy`
   - Surname: `Chen`
   - Revision date: 可留空或填写当天日期。
4. 创建后进入族谱详情页。

族谱详情页可以演示：

- Dashboard 成员统计。
- 成员管理入口。
- 后代树预览入口。
- 祖先查询入口。
- 关系路径查询入口。
- 协作者邀请区域。

## 4. 创建成员

进入族谱详情页的 `Manage members`，依次创建几个成员：

| Name | Gender | Birth year | Generation |
| --- | --- | --- | --- |
| Chen Grandfather | male | 1940 | 1 |
| Chen Father | male | 1965 | 2 |
| Chen Mother | female | 1968 | 2 |
| Chen Child | male | 1995 | 3 |

创建后回到成员列表，可以演示：

- 成员搜索。
- 成员表格。
- 成员详情页。
- 编辑成员资料。

## 5. 添加亲缘和婚姻关系

进入 `Chen Father` 的成员详情页，点击 `Relationships`。

建议添加：

1. 在 `Parents` 区域添加父亲：
   - Parent member ID: `Chen Grandfather` 的 ID。
   - Type: `father`。
2. 在 `Children` 区域添加子女：
   - Child member ID: `Chen Child` 的 ID。
   - Type: `father`。
3. 在 `Spouses` 区域添加配偶：
   - Spouse member ID: `Chen Mother` 的 ID。

关系管理页可以演示：

- Parents、Children、Spouses 三个分区。
- 添加关系表单。
- 删除关系按钮。

## 6. 后代树预览

回到族谱详情页，进入 `Tree Preview`。

输入：

```text
root_member_id = Chen Grandfather 的 ID
```

页面会显示从该成员开始的直系后代树。

## 7. 祖先查询

回到族谱详情页，进入 `Ancestor Query`。

输入：

```text
member_id = Chen Child 的 ID
```

页面会显示该成员向上追溯的祖先树。

## 8. 关系路径查询

回到族谱详情页，进入 `Relationship Path Query`。

输入：

```text
source_member_id = Chen Grandfather 的 ID
target_member_id = Chen Child 的 ID
```

页面会展示两人之间的亲缘路径。也可以输入 `Chen Father` 和 `Chen Mother` 的 ID，演示婚姻关系路径。

## 9. 演示检查点

演示时重点展示：

- 页面顶部导航是否清晰。
- 登录、注册、创建族谱、创建成员的表单是否易读。
- Dashboard、表格、卡片和查询结果是否有统一样式。
- 移动端窄屏下按钮和表格是否仍可操作。

UI-4 只负责前端演示和样式收尾。索引、性能对比和最终报告截图留到后续 milestone。
