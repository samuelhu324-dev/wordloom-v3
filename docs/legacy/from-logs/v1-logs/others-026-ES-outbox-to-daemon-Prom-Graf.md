有，而且你这痛点正是“监控体系存在的理由之一”：把 4–5 个终端窗口，压缩成 1 个网页页面。

这个仓库现在已经把“统一仪表盘”做成开箱即用：

- Prometheus：抓取你的 API/worker 的 /metrics
- Grafana：自动 provision 数据源 + Dashboard（无需手工 import）

你只需要跑一条 compose 命令。

---

## 一次到位：启动监控（dev + test 都看）

在仓库根目录执行：

```powershell
docker compose -f docker-compose.infra.yml --profile monitoring up -d
```

默认会同时抓 4 个 target（都在宿主机/WSL2 上跑）：

- dev API: host.docker.internal:30001/metrics
- dev worker: host.docker.internal:9108/metrics
- test API: host.docker.internal:30011/metrics
- test worker: host.docker.internal:9109/metrics

这些 target 定义在：

- docker/prometheus/prometheus.yml

如果你本机端口不一样，改这个文件里的端口即可。

---

## 验收（两分钟确认不折腾）

1) Prometheus targets 必须都是 UP：

- http://localhost:9090/targets

2) Grafana 登录：

- http://localhost:3000 （admin/admin）

3) Dashboard：

- 左侧 Dashboards → 进入 Wordloom 文件夹 → “Wordloom • Outbox + ES Bulk”

Dashboard 支持变量：

- env：dev/test（默认 All）
- projection：默认 All（bulk 指标存在时可筛选）

---

## 常见坑（只在抓取失败时看）

如果 targets 是 DOWN，99% 是容器访问宿主机地址问题：

- Windows/WSL2 + Docker Desktop：优先用 host.docker.internal（本仓库已使用）
- Linux 原生 Docker：需要 host-gateway/网关 IP（本仓库 compose 已加 extra_hosts=host-gateway，但你仍可能需要调整）