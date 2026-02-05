
# Wordloom 环境与启动指南（dev / test / sandbox）

这份文档的目标是把“本地要开一堆东西 + 环境混淆 + 测试误写开发库”的风险降到最低。

本仓库当前存在三种常用环境形态：

- **开发库（dev）**：日常开发使用，数据库为 `wordloom_dev`。
- **测试库（test）**：集成测试/压测/造流使用，数据库为 `wordloom_test`。
- **sandbox（全栈 compose）**：用根目录 `docker-compose.yml` 一键起 DB+后端+前端，适合“演示/快速看起来能跑”，不建议用于压测与造流。

> 推荐实践：**依赖用 Docker 管（DB/Elastic/监控），代码用 WSL2 跑（API/worker/loadgen）**。
> 这能让 FastAPI/SQLAlchemy/psycopg/httpx 行为更稳定，减少 Windows/WSL 混用导致的诡异问题。

---

## 1) 环境矩阵（端口/资源隔离）

当前仓库的“事实来源”如下：

- dev/test 数据库：根目录 `docker-compose.devtest-db.yml`（host 端口 **5435**）
- sandbox 全栈：根目录 `docker-compose.yml`（DB host 端口 **5434**，后端 **31001**，前端 **31002**）
- Elasticsearch：现在推荐由 infra-only compose 统一管理：根目录 [../../../docker-compose.infra.yml](../../../docker-compose.infra.yml)（host 端口 **9200**）

建议的端口约定（你已经在 QUICK_COMMANDS 里基本按这个在跑）：

| 环境 | Postgres host 端口 | DB 名 | API 端口 | worker metrics 端口 | Elasticsearch |
| --- | --- | --- | --- | --- | --- |
| dev | 5435 | wordloom_dev | 30001 | 9108 | http://localhost:9200 |
| test | 5435 | wordloom_test | 30011 | 9109 | http://localhost:9200 |
| sandbox | 5434 | wordloom | 31001 | （不建议） | （未纳入） |

> 说明：目前 dev/test 共用同一个 Postgres 容器，但用不同 DB 名隔离；如果你后续要进一步“物理隔离”，可以再拆成两个 compose/profile（见第 4 节计划）。

---

## 2) 需要单独开的服务（现状 + 未来扩展）

### 必开（当前链路：API → outbox → worker → Elasticsearch）

- **PostgreSQL（devtest-db-5435）**
	- 存储业务数据 + `search_index` + `search_outbox_events`。
	- dev/test 推荐使用它；sandbox 自带的 DB 端口不同（5434）。
- **Elasticsearch（9200）**
	- two-stage 的 stage1 recall 以及 outbox worker 的投影目标。
- **API（FastAPI/Uvicorn）**
	- 负责写入（创建 blocks/tags 等）并产生 outbox。
	- 也暴露 `/metrics`（produced 侧指标）。
- **Outbox worker**
	- 轮询 `search_outbox_events` 并写入 ES。
	- 自带一个 Prometheus exporter（默认 `9108`，test 推荐 `9109`）。

### 可选（当前就能用的观测方式）

- **curl/grep（最直接）**：
	- API produced：`curl -s http://localhost:30001/metrics | egrep '^outbox_produced_total'`
	- worker processed/failed/lag：`curl -s http://localhost:9108/metrics | egrep '^outbox_(processed_total|failed_total|lag_events)'`
- **直接查 DB（最准确）**：
	- `search_outbox_events where processed_at is null` 就是“积压”。

### 未来（Prometheus / Grafana / Loki 等）

短期你不需要上全家桶也能训练 throughput/lag，但后续要做“长期对比”和“可视化”，Prometheus 很值。

你可以按下面思路逐步引入（先不改代码）：

- Prometheus：scrape `API:30001/metrics` + `worker:9108/metrics`
- Grafana：导入 dashboard 看 produced/processed/lag 三条线

---

## 3) 各环境怎么启动（推荐跑法）

这里不把所有命令堆在一页（那会变成新的 QUICK_COMMANDS）。
命令细节请参考：

- [../docs_legacy/QUICK_COMMANDS.md](../docs_legacy/QUICK_COMMANDS.md)

下面只给“最小闭环”的顺序与关键变量。

### 3.0 先把 infra 起起来（Elastic + 可选监控）

从仓库根目录执行：

- 仅启动 Elasticsearch：
	- `docker compose -f docker-compose.infra.yml up -d es`
- 启动 Elasticsearch + Prometheus + Grafana：
	- `docker compose -f docker-compose.infra.yml --profile monitoring up -d`

检查：

- `curl http://localhost:9200/_cluster/health?pretty` 返回 `green/yellow`
- Prometheus（可选）：`http://localhost:9090`
- Grafana（可选，默认账号密码 admin/admin）：`http://localhost:3000`

### 3.1 dev（开发库：wordloom_dev@5435）

1）启动 Postgres（Windows PowerShell）

- 推荐走脚本：`backend/scripts/devtest_db_5435_start.ps1`

2）启动 Elasticsearch（Windows PowerShell）

- 推荐：用上面的 infra-only compose 启动 ES（第 3.0 节）。

3）启动 API（WSL2 / bash，建议端口 30001）

推荐使用 env 文件，避免手敲变量：

- 在仓库根目录：`.env.dev`

至少需要：

- `DATABASE_URL`（指向 `wordloom_dev@5435`）
- `ELASTIC_URL=http://localhost:9200`
- `ELASTIC_INDEX=wordloom-dev-search-index`

4）启动 worker（WSL2 / bash，metrics 9108）

- `DATABASE_URL` 同上
- `ELASTIC_URL/ELASTIC_INDEX` 同上
- `OUTBOX_METRICS_PORT=9108`

### 3.2 test（测试库：wordloom_test@5435，造流/压测）

目标：稳定跑通 `load_generate_blocks.py` → outbox produced → worker processed → ES 可检索。

1）启动 API（建议端口 30011，避免影响 dev）

推荐使用 env 文件：仓库根目录 `.env.test`。

2）启动 worker（建议 metrics 9109）

- `DATABASE_URL` 同上
- `OUTBOX_METRICS_PORT=9109`

3）跑造流脚本（WSL2 / bash）

- `API_BASE='http://localhost:30011'`
- `DATABASE_URL='postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test'`（用于自动选 book_id；或手动 `BOOK_ID=...`）
- 如果遇到超时：调大 `REQUEST_TIMEOUT_S`（默认 60 秒）。

### 3.3 sandbox（全栈 compose：不建议做压测/造流）

根目录 `docker-compose.yml` 会起：

- DB：`localhost:5434`（DB 名 `wordloom`）
- backend：`localhost:31001`
- frontend：`localhost:31002`

这个环境更像“演示盒子”。如果你要做 outbox/worker/ES 的吞吐训练，请优先用 devtest-db-5435 + 独立启动 API/worker/ES。

---

## 4) 你发的 env-deployment 计划：结合当前仓库，怎么一步步把环境管理到位

你给的思路（compose + profiles + dev/test 隔离 + sentinel 保险丝）非常正确。
结合当前仓库现状，我建议按“最小改动 → 稳定收益最大”的顺序推进：

### Step 0（现在就执行）：统一“环境事实来源”

- dev/test DB：只认 `docker-compose.devtest-db.yml`（host 5435）。
- sandbox：只认 `docker-compose.yml`（host 5434）。
- ES：先按现状用脚本起（`smoke_two_stage_elastic.ps1` 或手动 `docker run`），后续再纳入 compose。

### Step 1（立刻见效）：强制区分 dev/test 的“启动端口 + metrics 端口”

- API：dev 固定 30001；test 固定 30011。
- worker exporter：dev 固定 9108；test 固定 9109。
- QUICK_COMMANDS 里已经基本这样跑了，继续坚持即可。

### Step 2（立刻见效）：把 ES index 命名按环境隔离

目前很多地方默认 `ELASTIC_INDEX=wordloom-search-index`。
建议约定：

- dev：`wordloom-dev-search-index`（已写入 `.env.dev`）
- test：`wordloom-test-search-index`（已写入 `.env.test`）

这样即便 dev/test 共用同一个 ES，也不会互相覆盖。

### Step 3（开始“减少记忆负担”）：引入显式 env 文件（不必一次性容器化）

你可以先不动代码/compose，仅新增两套环境变量清单，并让所有启动命令引用它们：

- `.env.dev`：指向 `wordloom_dev@5435`、API 30001、worker 9108、ES index dev
- `.env.test`：指向 `wordloom_test@5435`、API 30011、worker 9109、ES index test

目标是：以后“想跑 dev/test”只需要选对 env 文件，而不是靠手敲 `DATABASE_URL`。

### Step 4（结构升级但不难）：新增一个“infra-only compose”（可选）

已完成：新增 [../../../docker-compose.infra.yml](../../../docker-compose.infra.yml)

- 默认只起 Elasticsearch（服务名 `es`）
- `--profile monitoring` 会额外启动 Prometheus/Grafana

### Step 5（救命保险丝）：DB Sentinel（强烈建议）

已完成（最小可用版本）：

- DB 层新增 `environment_sentinel` 表（migrate 会创建；devtest-db 初始化时也会自动创建）。
- API / outbox worker 启动时会读取 `WORDLOOM_ENV` 并校验当前连接的 DB（不匹配直接拒绝启动）。

这是最能防止“连错库/炸库”的措施：

- 在每个 DB 放一条元信息（env=dev/test, project=wordloom）。
- API/worker 启动时检查：`ENV=test` 就必须连到 sentinel=test 的库；不匹配直接退出并打印“你连错库了”。
- 所有 destructive 脚本（重置、drop、migrate）也必须做同样检查。

> 现状说明：
> - `devtest_db_5435_migrate.ps1` 已经对 host/port/dbname 做了强校验（只允许 localhost:5435 + wordloom_dev|wordloom_test）。
> - “drop/reset” 级别的 destructive 脚本如果你后续要加，我建议也复用同样的 sentinel 校验逻辑。

---

## 6) 一键启动（推荐）

目标：把“多窗口 + 记命令 + 切环境”收敛成一个入口。

### 6.1 安装 app 进程管理器（WSL2）

我们用 Procfile/honcho 来拉起：API + worker + Next。

```bash
python3 -m pip install --user honcho

# 如果提示找不到 honcho，一般是 PATH 没包含 ~/.local/bin
export PATH="$HOME/.local/bin:$PATH"
```

### 6.2 一键启动（WSL2）

从仓库根目录（建议 WSL2）：

```bash
# dev：infra + db + migrate + (api + worker + ui)
./scripts/up.sh dev

# test：infra + db + migrate + (api + worker + ui)
./scripts/up.sh test
```

如果遇到 `Permission denied`，先执行一次：

```bash
chmod +x scripts/*.sh backend/scripts/*.sh
```

如果你想拆开来控制（比如先起 infra / db，再单独重启 app）：

```bash
# infra
./scripts/infra_up.sh es
# 或：./scripts/infra_up.sh monitoring

# dev/test DB (localhost:5435)
./scripts/db_up.sh

# migrate
./scripts/db_migrate.sh dev
./scripts/db_migrate.sh test

# app layer (Procfile)
./scripts/app_up.sh dev
./scripts/app_up.sh test
```

说明：
- `Procfile.dev` / `Procfile.test` 定义了 API、worker、UI 三个进程。
- `.env.dev` / `.env.test` 会被导出到所有进程，避免“跑起来但其实连错环境”。

---

## 5) 常见故障快速判断（节省时间）

- ES `curl localhost:9200` 偶发 reset：通常是“容器已启动但还没 ready”，等到 `/_cluster/health` 有响应再继续。
- worker 不动：先看 worker exporter 的 `outbox_lag_events`；再查 DB 的 `search_outbox_events processed_at is null`。
- loadgen 超时：调大 `REQUEST_TIMEOUT_S`，并确认 `API_BASE` 指向正确端口（dev 30001 / test 30011）。

### PowerShell 提醒：不要把 /metrics 当成脚本跑

Prometheus 的 `/metrics` 输出里包含大量 `{}`，在 Windows PowerShell 里如果你把输出“误粘贴成命令的一部分”，会触发各种解析错误（看起来像是 `python_info{...}` 之类的内容在报错）。

建议：

- Windows 下用 `curl.exe http://localhost:30001/metrics | findstr outbox_`
- 或者在 WSL2 里用 `curl -s http://localhost:30001/metrics | egrep '^outbox_'`

