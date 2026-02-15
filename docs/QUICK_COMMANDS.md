## 后端启动（WSL2）

> 建议：把依赖（Elastic/监控）统一交给 infra-only compose 管；dev/test 用 `.env.dev/.env.test` 固定住变量，避免环境混淆。

### 一键启动（WSL2：推荐）

目标：解决“多窗口开一堆 + 记一堆命令 + 切虚拟环境”的麻烦。

1）在 WSL2 安装 honcho（Procfile 进程管理）：

```bash
python3 -m pip install --user honcho
export PATH="$HOME/.local/bin:$PATH"
```

2）一键启动（含 infra + devtest-db + migrate + app）：

```bash
cd /mnt/d/Project/wordloom-v3

# 如果第一次跑提示 Permission denied：
# chmod +x scripts/*.sh backend/scripts/*.sh
z
# dev（API:30001 / worker metrics:9108 / ES index: wordloom-dev-search-index）
./scripts/up.sh dev

# test（API:30011 / worker metrics:9109 / ES index: wordloom-test-search-index）
./scripts/up.sh test

# 只启动 API+UI（不启动 worker；用于先排查 ES/Jaeger/DB 等环境）
./scripts/up.sh test --no-worker
```

只拉起 app 进程（不动 infra/db）也可以：

```bash
./scripts/app_up.sh dev
./scripts/app_up.sh test
```

infra-only compose（从仓库根目录）：

```bash
cd /mnt/d/Project/wordloom-v3

# 仅 ES
docker compose -f docker-compose.infra.yml up -d es

# ES + 监控（Prometheus + Grafana）
docker compose -f docker-compose.infra.yml --profile monitoring up -d
```

监控入口：

- Prometheus targets：`http://localhost:9090/targets`
- Grafana：`http://localhost:3000`（admin/admin）→ Dashboards → Wordloom 文件夹 → “Wordloom • Outbox + ES Bulk”
	- 新增面板：`Net rate (processed - produced) /s`、`429 ratio (bulk item failures / items)`（带 1% 参考线）

```
$env:PYTHONPATH="d:\Project\WordloomLegacy\WordloomBackend\api" ; python -m uvicorn app.main_orbit:app --reload --host 127.0.0.1 --port 18080

$env:PYTHONPATH="d:\Project\WordloomLegacy\WordloomFrontend\next" ;  npm run dev -- --hostname 127.0.0.1 --port 6001
```

### 快速启动（已安装依赖）

```
cd /mnt/d/Project/wordloom-v3/frontend
npm run dev
npm run test:e2e
or specifically, say:
npm run test:e2e -- --list
npx playwright test --project=chromium --grep \"LIB-OVW\" 
```

```
cd /mnt/d/Project/wordloom-v3/backend

export DATABASE_URL="postgresql://wordloom:wordloom@localhost:5435/wordloom_dev"
export SEARCH_STAGE1_PROVIDER=elastic
export ELASTIC_URL=http://localhost:19200
export ELASTIC_INDEX=wordloom-dev-search-index

uvicorn api.app.main:app --host 0.0.0.0 --port 30001 --reload 2>&1 | tee server.log
```

#### Outbox worker（WSL2 / bash）

推荐（少手敲变量，且带防混库校验）：

```bash
# dev
./backend/scripts/ops/run_worker.sh .env.dev

# test
./backend/scripts/ops/run_worker.sh .env.test
```

常见报错速查（ES 明明在跑但 worker 仍报协议/断连类错误）：

- 先用 curl 验证 ES 是 HTTP 还是 HTTPS：
	- `curl -sv http://localhost:19200/ | head -n 20`
	- 若你误用 `https://localhost:19200` 连接一个纯 HTTP 的 ES，会看到类似 `wrong version number`。
- 确认 `ELASTIC_URL/ELASTIC_INDEX` 没有被设置成空字符串（空字符串会覆盖默认值）：
	- `echo "ELASTIC_URL=$ELASTIC_URL"`
	- `echo "ELASTIC_INDEX=$ELASTIC_INDEX"`

```bash
cd /mnt/d/Project/wordloom-v3/backend
source .venv_linux/bin/activate  # 如有

export DATABASE_URL='postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_dev'
export ELASTIC_URL='http://localhost:19200'
export ELASTIC_INDEX='wordloom-dev-search-index'

# 兼容入口（稳定路径）：backend/scripts/search_outbox_worker.py
python3 scripts/search_outbox_worker.py
```

#### Outbox worker 参数（bulk / concurrency / poll）

默认值：

- `OUTBOX_BULK_SIZE=100`
- `OUTBOX_CONCURRENCY=1`
- `OUTBOX_POLL_INTERVAL_SECONDS=1.0`（或用 `OUTBOX_POLL_INTERVAL_MS` 覆盖）
- `OUTBOX_METRICS_PORT=9108`
- `OUTBOX_USE_ES_BULK=0`（可选：开启后用 ES Bulk API，每轮 poll 1 次 `POST /_bulk`）

WSL2 / bash 示例（更快拉取 + 并发处理）：

```bash
export OUTBOX_BULK_SIZE=500
export OUTBOX_CONCURRENCY=8
export OUTBOX_POLL_INTERVAL_MS=200

python3 scripts/search_outbox_worker.py
```

WSL2 / bash 示例（开启 ES Bulk API；更适合做 bulk 实验）：

```bash
export OUTBOX_USE_ES_BULK=1
export OUTBOX_BULK_SIZE=500
export OUTBOX_POLL_INTERVAL_MS=200

python3 scripts/search_outbox_worker.py
```

> 注意：Bulk 模式下 worker 每轮只发一个 bulk 请求，`OUTBOX_CONCURRENCY` 会被忽略（以日志提示为准）。

Windows PowerShell 示例：

```powershell
$env:OUTBOX_BULK_SIZE = "500"
$env:OUTBOX_CONCURRENCY = "8"
$env:OUTBOX_POLL_INTERVAL_MS = "200"
$env:OUTBOX_METRICS_PORT = "9108"

python backend/scripts/search_outbox_worker.py
```

建议做 bulk 实验时只改 1 个参数，然后看：

- `sum(rate(outbox_processed_total{projection="search_index_to_elastic"}[1m]))`
- `max(outbox_lag_events{projection="search_index_to_elastic"})`

如果开启 `OUTBOX_USE_ES_BULK=1`，再额外看：

- bulk 耗时：`outbox_es_bulk_request_duration_seconds`
- bulk 是否 partial：`outbox_es_bulk_requests_total{result="partial"}`
- 失败分类：`outbox_es_bulk_item_failures_total{failure_class="429"|"4xx"|"5xx"|"unknown"}`

#### Outbox 观测自测（Tag → outbox → metrics）

目标：验证 `Tag` 创建会写入 `search_outbox_events`，并让 `outbox_produced_total{event_type,entity_type}` 增长；同时 worker 会暴露 `processed/failed/lag`。

1）确认后端 metrics（API 进程）可访问

```bash
curl -s http://localhost:30001/metrics | grep outbox_produced_total
```

2）创建一个 Tag（触发 produced）

```bash
curl -s -X POST http://localhost:30001/api/v1/tags \
	-H 'content-type: application/json' \
	-d '{"name":"tag-metrics-smoke","color":"#22c55e"}'
```

3）检查 DB 是否写入 outbox（PowerShell，先找到容器名）

```powershell
docker ps --format "{{.Names}}" | Select-String -Pattern "devtest"
```

然后（把容器名替换成你的实际输出，例如 wordloom-devtest-db_devtest-1）：

```powershell
docker exec -it wordloom-devtest-db_devtest-1 psql -U wordloom -d wordloom_dev -c "select entity_type, op, created_at from search_outbox_events order by created_at desc limit 10;"
```

4）确认 produced 计数器出现样本行（不再只有 HELP/TYPE）

```bash
curl -s http://localhost:30001/metrics | grep 'outbox_produced_total{'
```

预期能看到类似：

```text
outbox_produced_total{event_type="tag.created",entity_type="tag"} 1
```

5）启动 worker metrics 端口（worker 默认监听 `9108`）

```bash
export OUTBOX_METRICS_PORT=9108  # 可选，默认就是 9108
python3 scripts/search_outbox_worker.py
```

然后另开一个终端：

```bash
curl -s http://localhost:9108/metrics | grep outbox_
```

6）Grafana 三条线（PromQL）

- produced/s：
	- `sum(rate(outbox_produced_total[1m]))`
	- 分 event_type：`sum by (event_type) (rate(outbox_produced_total[1m]))`
- processed/s：
	- `sum(rate(outbox_processed_total{projection="search_index_to_elastic"}[1m]))`
- lag_events：
	- `max(outbox_lag_events{projection="search_index_to_elastic"})`

判读：`produced/s > processed/s` 持续一段时间 → `lag_events` 会一路上升（积压）；反之趋于稳定。

#### Outbox 压测（Blocks 注入到 wordloom_test）

目标：在 `wordloom_test` 里批量创建 blocks，观察 `produced/processed/lag` 三条线。

1）启动 API（连 wordloom_test，建议用独立端口避免影响 dev）

推荐（少手敲变量，且带防混库校验）：

```bash
./backend/scripts/ops/run_api.sh .env.test
```

```bash
cd /mnt/d/Project/wordloom-v3/backend
export DATABASE_URL='postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test'
uvicorn api.app.main:app --host 0.0.0.0 --port 30011 --reload 2>&1 | tee server_test.log
```

2）启动 worker（连 wordloom_test，metrics 用独立端口）

```bash
cd /mnt/d/Project/wordloom-v3/backend
export DATABASE_URL='postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test'
export ELASTIC_URL='http://localhost:19200'
export ELASTIC_INDEX='wordloom-test-search-index'
export OUTBOX_METRICS_PORT=9109

python3 scripts/search_outbox_worker.py
```

3）批量注入 blocks（走 API，会自动从 DB 选一个 book_id；也可手动指定 BOOK_ID）

```bash
cd /mnt/d/Project/wordloom-v3/backend
export API_BASE='http://localhost:30011'
export DATABASE_URL='postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test'

export TOTAL_BLOCKS=5000
export RATE_PER_SEC=50
export CONCURRENCY=10
export BLOCK_TYPE=text
export CONTENT_BYTES=200

python3 scripts/load_generate_blocks.py
```

4）怎么监控（不依赖 Prometheus，也能用 curl 先练习）

```bash
# 写入侧 produced（API 进程）
curl -s http://localhost:30011/metrics | egrep '^outbox_produced_total'

# worker 侧 processed/failed/lag
curl -s http://localhost:9109/metrics | egrep '^outbox_(processed_total|failed_total|lag_events)'

# bulk 指标（如果开启了 OUTBOX_USE_ES_BULK=1）
curl -s http://localhost:9109/metrics | egrep '^outbox_es_bulk_'
```

5）可选：从 DB 直接看积压（PowerShell）

```powershell
docker exec -it wordloom-devtest-db_devtest-1 psql -U wordloom -d wordloom_test -c "select count(*) as pending from search_outbox_events where processed_at is null;"
```

# 一键自测：Elastic Stage1 + Postgres Stage2（会等待 health=200 再请求 two-stage）
# PowerShell:
#   .\backend\scripts\smoke_two_stage_elastic.ps1 -Port 30002 -Query "quantum" -RecreateIndex
```

## 开发/测试数据库（DEVTEST-DB-5435，推荐）

目标：在本机 `localhost:5435` 跑一套**独立**的 Postgres（一个容器里包含 `wordloom_dev` + `wordloom_test` 两个数据库），专用于开发/pytest，避免和其他 compose / sandbox 混用。

### 启动/停止（Windows PowerShell）
```powershell
# 依赖：Docker Desktop 已启动（否则会报 docker pipe 找不到）

cd d:\Project\Wordloom

# 启动 DEVTEST Postgres（端口 5435）
.\backend\scripts\devtest_db_5435_start.ps1

# 停止
.\backend\scripts\devtest_db_5435_stop.ps1
```

### 初始化/重置（⚠ 会删除数据）
```powershell
cd d:\Project\Wordloom

# DESTROY ALL DATA：重置 volume，重新执行 docker/postgres/init 下的 init 脚本
docker compose -f .\docker-compose.devtest-db.yml -p wordloom-devtest down -v
docker compose -f .\docker-compose.devtest-db.yml -p wordloom-devtest up -d
```

### 迁移（Alembic upgrade head，带安全保护）
说明：脚本会**拒绝**对非 `localhost:5435/(wordloom_dev|wordloom_test)` 执行迁移，防止误操作。

```powershell
cd d:\Project\Wordloom

# migrate dev
.\backend\scripts\devtest_db_5435_migrate.ps1 -Db wordloom_dev

# migrate test（pytest 用）
.\backend\scripts\devtest_db_5435_migrate.ps1 -Db wordloom_test
```

### 跑 pytest（会先 migrate test DB）
```powershell
cd d:\Project\Wordloom

# 默认：-q api/app/tests
.\backend\scripts\devtest_db_5435_run_pytest.ps1

# 指定参数
.\backend\scripts\devtest_db_5435_run_pytest.ps1 -Args "-q api/app/tests/test_integration_four_modules.py"
```

### 后端使用 dev 库启动（可选）
如果你希望后端也显式连到 `wordloom_dev@localhost:5435`，可以在启动前覆盖环境变量：

```powershell
cd d:\Project\Wordloom\backend
$env:DATABASE_URL = "postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_dev"
python -m uvicorn api.app.main:app --host 0.0.0.0 --port 30001 --reload
```

## 前端启动（Windows PowerShell）
```powershell
cd d:\Project\Wordloom\frontend
npm install

# 推荐：明确选择后端环境（不再靠一个 .env.local 混用）
# - dev 后端：30001
npm run dev:dev
# - test 后端：30011
# npm run dev:test
# - sandbox 后端（docker-compose.yml）：31001
# npm run dev:sandbox
```

## 目录导航
```bash
cd /mnt/d/Project/Wordloom/frontend
cd /mnt/d/Project/Wordloom/backend
```

wsl

sudo service postgresql status
# 或者有些系统是：
sudo systemctl status postgresql

sudo service postgresql start
# 或
sudo systemctl start postgresql

永远用同一条命令跑真库测试，不要手工 set DATABASE_URL：
cd D:\Project\wordloom-v3
.\backend\scripts\devtest_db_5435_run_pytest.ps1 -Args "-vv backend\api\app\tests\test_repo_contracts\test_cover_bind_repo_contracts.py"

