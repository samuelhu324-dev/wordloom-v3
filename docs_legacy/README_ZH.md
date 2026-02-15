# Wordloom

---

## 项目简介

- Wordloom 是一个个人知识管理（PKM）工作台：以「知识库 / 书架 / 书籍 / 块」为核心组织内容，并支持标签、搜索与回收站（Basement）。
- 技术栈：Frontend 为 Next.js，Backend 为 FastAPI，数据库使用 PostgreSQL（通过 Docker 一键启动）。
- 适合场景：日常阅读摘录、长期写作素材整理、工作/学习的结构化笔记沉淀。

## Quick start (Docker)

```powershell
# 0) 选定路径
cd <any path>

# 1) 克隆
git clone https://github.com/samuelhu324-dev/Wordloom.git Wordloom

# 2) 进入仓库
cd Wordloom
 
# 3) 复制容器环境
copy backend\.env.docker.example backend\.env.docker
copy frontend\.env.docker.example frontend\.env.docker

# 4) 启动（需提前安装并启动 Docker Desktop）
docker compose up -d --build

# 5) 打开（Frontend）
# http://localhost:31002
```

<!--

Prereq: Docker/Desktop running; Alembic runs via backend/entrypoint.sh; DB exposed 5432(container)/5434(host).

-->
