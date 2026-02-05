# 一键启动（WSL2 推荐，dev/test 分离）

本项目已收敛为：
- **infra**：Docker Compose（ES/监控等）
- **app 层**（API + worker + Next）：Procfile + honcho（在 WSL2 内启动）
- **dev/test**：使用根目录 `.env.dev` / `.env.test` 与 `Procfile.dev` / `Procfile.test` 明确分离，避免误连库。

---

## 0) 前置条件（只做一次）

在 **WSL2** 中：

1) Node / npm 可用（前端跑在 WSL2）

```bash
node -v
npm -v
```

2) 安装 honcho（用于跑 Procfile，多进程一键拉起）

```bash
python3 -m pip install --user honcho
# 如果 ~/.local/bin 没在 PATH：
# echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
honcho --version
```

3) Docker Desktop 已启用 WSL integration（infra/db 需要）

```bash
docker version
```

---

## 1) 一键启动（推荐入口）

从仓库根目录执行：

### 启动 test 环境

```bash
cd /mnt/d/Project/wordloom-v3
bash scripts/up.sh test
```

### 启动 dev 环境

```bash
cd /mnt/d/Project/wordloom-v3
bash scripts/up.sh dev
```

这个命令会按顺序完成：
1) 起 ES（`docker-compose.infra.yml`）
2) 起 dev/test DB（localhost:5435，使用 `backend/scripts/devtest_db_5435_start.ps1`）
3) migrate 对应数据库（dev→`wordloom_dev`，test→`wordloom_test`）
4) 用 honcho 启动 app 层三进程（`Procfile.dev` / `Procfile.test`）：
   - `api: bash ./backend/scripts/run_api.sh .env.(dev|test)`
   - `worker_search: bash ./backend/scripts/run_worker.sh .env.(dev|test)`
   - `ui: cd frontend && npm run dev:(dev|test)`

---

## 2) 访问地址（默认）

- UI（Next）：http://localhost:30002
- API（dev）：http://localhost:30001
- API（test）：http://localhost:30011
- ES：http://localhost:9200

---

## 3) 停止 / 重启

### 停止 app（API + worker + UI）
在运行 `honcho` 的终端按 `Ctrl + C`。

### 停止 infra（ES）

```bash
cd /mnt/d/Project/wordloom-v3
docker compose -f docker-compose.infra.yml down
```

（DB 使用的是 devtest compose 工程；如需停止 DB，请运行 Windows 侧对应 stop 脚本或 `docker compose -f docker-compose.devtest-db.yml -p wordloom-devtest down`。）

---

## 4) 常见卡点（快速自救）

### 4.1 提示缺少 honcho

```bash
python3 -m pip install --user honcho
```

### 4.2 端口被占用（EADDRINUSE / Address already in use）

一键启动前可先跑 preflight（会检查：WSL + Windows 两边的占用）：

```bash
cd /mnt/d/Project/wordloom-v3
bash scripts/preflight.sh test
# 或
bash scripts/preflight.sh dev
```

如果确实有占用：
- WSL 内查占用：
  ```bash
  ss -ltnp | grep ':30002\|:30001\|:30011\|:9108\|:9109'
  ```
- Windows 上查占用：
  ```powershell
  netstat -ano | findstr ":30002"
  ```

注意：**UI 的 30002 冲突很多时候来自 Windows 侧残留的 Next/Node**（即使你现在在 WSL 跑 UI）。
可以用下面命令确认并停止（把 PID 换成 netstat 查到的）：

```powershell
Get-Process -Id 24196 | Format-List Id,ProcessName,Path
Stop-Process -Id 24196 -Force
```

### 4.3 Next 在 WSL 下缓存/权限异常

```bash
cd /mnt/d/Project/wordloom-v3/frontend
rm -rf .next .next-dev .turbo
```

---

## 5) 推荐工作流（按需开机）

- 日常开发（推荐）：`bash scripts/up.sh dev` + 只关注 1~2 个 worker
- 做集成回归：`bash scripts/up.sh test`
- 只调 UI：确保 API 已起（dev/test），再单独跑 `npm run dev:dev` 或 `npm run dev:test`

---

## 6) 相关入口（你可以按需点进看）

- `Procfile.dev` / `Procfile.test`
- `scripts/up.sh`（一键启动总入口）
- `scripts/preflight.sh`（一键启动前置检查）
- `scripts/app_up.sh`（只起 app 层）
- `scripts/infra_up.sh`（只起 infra）
- `scripts/db_up.sh` + `scripts/db_migrate.sh`（WSL 调 PowerShell 跑 DB 与 migrate）

---

## 7) 后端虚拟环境（重要）

`Procfile.dev/test` 会调用：
- `backend/scripts/run_api.sh`
- `backend/scripts/run_worker.sh`

这两个脚本会自动选择 Python 运行环境：
- 若已在虚拟环境中（`VIRTUAL_ENV` 存在）→ 直接使用
- 若存在 `backend/.venv` 或 `backend/.venv_linux` → 自动 `source .../bin/activate`
- 否则若 `poetry` 可用 → 使用 `poetry run ...`
- 都没有 → 直接报错并给出创建 venv 的命令
