# 攻略聚类站后端 · 第一版

Python 3.12+ / FastAPI / SQLAlchemy 2 / Alembic / PostgreSQL / Pydantic 2。
目前实现 Creator → Guide → Comment 三张表及 CRUD，以及 B 站视频和公开评论导入；
不包含 Agent、任务队列或向量检索。

项目的设计与开发对话整理在 [docs/conversation.md](docs/conversation.md)。

## 一键启动（推荐）

安装并启动 Docker Desktop（支持 Docker Compose v2），进入本目录：

```powershell
Copy-Item .env.example .env
docker compose up --build -d
```

macOS / Linux 将第一行改为 `cp .env.example .env`。

Compose 会等待 PostgreSQL 就绪、执行 Alembic 迁移，再启动 API。
打开 http://localhost:8000/docs 即可在 Swagger UI 里创建和查询数据。

- 存活检查：`GET /health`
- 数据库与表就绪检查：`GET /health/ready`
- 日志：`docker compose logs -f api migrate`
- 停止：`docker compose down`（保留数据库卷）
- 修改代码后：重新运行 `docker compose up --build -d`

默认数据库和 API 仅绑定本机。此版本没有登录鉴权，适合本地开发。
`.env.example` 内为开发密码；如需修改账号、密码或数据库名，同时更新
`DATABASE_URL` 和 `POSTGRES_*`。连接串中的特殊字符需 URL 编码。
数据库已初始化后，修改 `POSTGRES_*` 不会自动修改已有数据库账户。

## Python 本地启动

需要 Python 3.12+，数据库可由 Docker 或已有 PostgreSQL 16 提供。
以下命令均在 `backend/` 目录执行：

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
docker compose up -d db
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

macOS / Linux 对应使用 `python3` 创建环境，随后使用 `.venv/bin/python`。
已有 PostgreSQL 时跳过启动 db，修改 `.env` 中的 `DATABASE_URL`。
若修改 `POSTGRES_PORT`，也需同步本地 `DATABASE_URL` 的端口。
全容器模式会自动使用数据库服务的内部地址。

数据库由 Alembic 管理；应用启动不会自行建表。

## 目录

```text
backend/
├── app/
│   ├── main.py
│   ├── api/          # creators.py / guides.py / comments.py
│   ├── models/       # SQLAlchemy 数据表
│   ├── schemas/      # Pydantic 请求和响应
│   ├── services/     # CRUD 与事务处理
│   └── core/         # 配置、数据库连接和会话
├── alembic/          # 版本化迁移
├── tests/            # 冒烟及真实 PostgreSQL 集成测试
├── .env.example
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## API

| 资源 | 列表与新增 | 详情、局部更新、删除 | 列表筛选 |
| --- | --- | --- | --- |
| 作者 | GET / POST `/creators` | GET / PATCH / DELETE `/creators/{id}` | platform |
| 攻略 | GET / POST `/guides` | GET / PATCH / DELETE `/guides/{id}` | creator_id、platform |
| 评论 | GET / POST `/comments` | GET / PATCH / DELETE `/comments/{id}` | guide_id |

### 导入 B 站视频

调用 `POST /imports/bilibili/videos`，`video` 可以传 BV 号或完整视频链接：

```json
{
  "video": "https://www.bilibili.com/video/BV1Wz411B7Wn",
  "fetch_comments": true,
  "max_comments": 100
}
```

接口会幂等更新作者、攻略及评论。重复导入不会生成重复记录，响应会分别给出
作者和攻略是否为新建，以及评论的抓取、新建和更新数量。

评论按 B 站网页端顺序抓取，目前每次最多 500 条；返回页中携带的楼中楼回复也会入库。
部分视频关闭评论，或公开接口触发限流时，接口可能返回 429。可在本机 `.env` 中设置
`BILIBILI_COOKIE` 后重试；不要提交包含 Cookie 的 `.env`，也不要使用他人的登录信息。
只需要视频元数据时，可设置 `fetch_comments=false`。

采集器默认遵循系统代理环境变量。如代理配置不可用，可在 `.env` 设置
`BILIBILI_TRUST_ENV=false` 改为直接连接。

B 站网页接口可能调整字段或风控规则。采集器使用请求超时、匿名设备标识和 WBI 签名，
不会在上游失败时写入半成品数据；生产环境仍应增加低频队列、重试退避和来源合规检查。

列表返回 JSON 数组，支持 `offset=0&limit=20`，limit 最大为 100；
按 created_at、id 升序排列。主键为 UUID。

新增返回 201；删除返回 204；不存在返回 404；输入不合法返回 422；
平台标识重复、外键不存在或记录仍被引用返回 409。
PATCH 仅修改传入字段，可空字段支持传入 null 清空；必填字段不能清空。
时间输入必须带时区，如 `2026-09-24T10:00:00+08:00`。

### 在 Swagger 中依次尝试

1. POST `/creators`：

```json
{"platform": "bilibili", "platform_creator_id": "123456", "name": "攻略作者"}
```

2. 将响应 id 填入 POST `/guides` 的 creator_id：

```json
{
  "creator_id": "替换为作者 UUID",
  "platform": "bilibili",
  "platform_content_id": "BV_DEMO_001",
  "title": "太刀新手攻略",
  "url": "https://www.bilibili.com/video/BV_DEMO_001",
  "description": "测试数据",
  "published_at": "2026-09-24T10:00:00+08:00"
}
```

3. 将攻略 id 填入 POST `/comments`：

```json
{
  "guide_id": "替换为攻略 UUID",
  "platform_comment_id": "10001",
  "content": "适合新手，步骤清晰。",
  "likes": 12
}
```

随后可查询 `/guides?creator_id=...` 和 `/comments?guide_id=...`。

## 数据约定

- 作者唯一键：(platform, platform_creator_id)。
- 攻略唯一键：(platform, platform_content_id)。
- 评论唯一键：(guide_id, platform_comment_id)。
- guide.creator_id、comment.guide_id 为数据库外键，并建索引。
- parent_comment_id 保存**平台原始评论 ID**，不是本库 UUID，也不是外键；
  允许先采集回复，随后采集父评论。
- 删除使用 RESTRICT：先删评论，再删攻略，最后删作者。
- followers、点赞和播放量等计数不能为负，数据库也有 CHECK 约束。
- description、transcript、平台链接、采集时间等可空字段允许后续补齐。
- created_at 由数据库赋值；updated_at 在 ORM 更新时刷新。
- 暂不创建 Game 表或无约束的 game_id，后续通过迁移增加。
- B 站导入会根据标题和简介计算 content_hash。内容发生变化时，analysis_status 重置为
  pending；成功采集后 crawl_status 为 crawled。
- 手工 CRUD 仍允许调用方直接维护 content_hash 和状态字段。

## 迁移与测试

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic check
.\.venv\Scripts\python.exe -m pytest -q
```

未设置 TEST_DATABASE_URL 时仅运行无数据库冒烟测试，集成测试会明确跳过。
完整测试使用 PostgreSQL：

```powershell
$env:TEST_DATABASE_URL = "postgresql+psycopg://guide:guide_dev_password@localhost:5432/guide_cluster"
.\.venv\Scripts\python.exe -m pytest -q
```

测试账号需有 CREATE SCHEMA 权限。测试会创建随机独立 schema，
执行迁移升级、模型差异检查、降级、重新升级，再验证 CRUD、约束和事务回滚；
结束后仅删除测试创建的 schema，不清空业务表。

新增迁移：`python -m alembic revision --autogenerate -m "describe change"`，
人工检查迁移后再运行 `python -m alembic upgrade head`。

## 本次验证

已使用 Python 3.12 和真实 PostgreSQL 16 完成 9 项测试，
包括迁移升级、降级、再次升级及模型差异检查；Ruff 检查通过。
实际启动 Uvicorn 后，health、ready、docs、openapi.json 和 creators 均返回 200。
测试服务已停止。当前机器未安装 Docker，因此 Compose 仅验证了 YAML 配置，
尚未实际构建和运行容器。测试依赖有一条来自 Starlette 的 httpx 弃用提示，
不影响本次测试结果。
