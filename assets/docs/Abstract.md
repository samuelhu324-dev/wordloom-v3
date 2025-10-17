# **Chat Overview**  
**Reference Period:** 2025-10-15 → 2025-10-??  
**Context:** Functional refinement and feature restructuring of the Translation Retriever System.

## **1 · Wordloom**

### 1. 最小全栈闭合

...

二、我需要你提供的文件（用来分析与改造）

1. 后端（WordloomBackend/api/app/ 为主结构）

请把以下文件发给我，我要看代码内容以便统一逻辑：

app/models.py —— ORM 模型（数据库表结构）

app/schemas.py —— Pydantic 模型（接口输入输出）

app/repo.py —— 数据操作层（我会把逻辑抽到 service）

app/database.py —— 数据库连接和 Session 管理

app/main.py 或 app/app.py —— FastAPI 启动入口

app/routers/*.py —— 路由文件（尤其是 entries.py, sources.py, auth.py）

.env —— 可以去掉密码和密钥，只保留变量名我看结构

core/repo.py —— 似乎和上面的 repo 重复，我要对比后整合

storage/wordloom.db —— 当前的主数据库文件

我会以 app/ 为主，整合掉 backend/ 那个重复层。

2. 前端（WordloomFrontend/streamlit/）

我会帮你把所有直接访问数据库的部分，改为访问 API：

repo.py、models.py —— 这些文件应该现在还在直接用 SQLite，我会改成调用 API；

app.py —— 主入口，我会保留 UI，注入 client = ApiClient(...)；

pages/0_??_Home_Admin.py, 1_??_From_Page.py, 2_??_Insert.py, 3_??_Bulk_Insert_plus_status.py —— 这些页面里凡是操作数据库的地方，我都会改为 client.xxx()；

import_csv.py、export_csv.py 等辅助脚本——如果读写数据库，我也会改成调用接口。

三、我会新增的文件（后端 + 前端）
A. 后端新增

为了解耦和规范化，我会增加以下模块：

文件	功能
config.py	用 Pydantic 管理 .env 配置变量（数据库路径、CORS、密钥等）
services/	放业务逻辑，比如 entries_service.py, sources_service.py
deps.py	放依赖注入（获取数据库 Session、当前用户等）
errors.py	自定义错误类 + 全局错误处理
security.py	JWT 鉴权、密码哈希等功能
openapi_tags.py	给接口文档分组（更易读）
static/	可选：如果你想让后端直接托管 assets/static 文件
alembic/ + alembic.ini	数据库迁移系统（防止表结构错乱）
tests/	用 pytest 做基本接口测试
.env.example	环境变量示例文件（开发者参考）
B. 前端新增

为 Streamlit 创建一个独立的 API 调用层：

文件	功能
api_client.py	封装请求，用于调用后端接口（类似 SDK）
settings.py	存放后端地址（API_BASE_URL）
state.py	Streamlit session 状态管理（保存 JWT 等）
adapters/	可选，做数据结构转换，让 UI 层更简洁

四、我会删除或合并的内容

core/repo.py —— 如果和 app/repo.py 重复，就合并成一个；

app/app.py 或 backend/app.py —— 保留一个统一入口（main.py）；

database.py.bak 等旧备份文件——迁移后删除；

旧的 backend/ 目录 —— 若无新功能，完全移除。

### 2. 闭合后规划：

1. 四页功能逐一核查（不改逻辑，只验流）

Home_Admin：是否已改为通过新 repo.client 读/改条目，并保持你原来的管理入口与筛选习惯。

From_Page：按“文章=一个出处”的阅读视图，验证顺序显示、以及中途插入句子的交互是否使用了 client.create_article / insert_sentence / get_article_sentences 这一套。

Insert：单条入库用 client.add_entry，默认语言方向与你之前一致（en→zh 的默认在批量页已固化；单条也保持一致性）。

Bulk_Insert_plus_status：三路合并（CSV/粘贴/手填）→去重→逐条 add_entry，看进度条与失败明细折叠是否正常；“预览匹配/批量替换”是否命中并返回修改数。

2. 源数据选择器（小升级，不变核心逻辑）

在 Home、Insert 与 Bulk 里，把“出处”输入框升级为可搜索下拉：前端在加载时调用 /sources 拉取列表缓存到 st.session_state["sources"]，下拉可输入过滤，也可手动输入新值（不破坏你既有行为）。后面我可以直接把“来源下拉”补丁发你。

3. 错误处理与提示统一

统一捕获 ApiError，配合 st.toast / st.error / st.warning 给出清晰反馈；页面底部保留 API_BASE 显示，便于你快速判断连的哪个环境。（Home.py 已这么做，其他三页同样风格对齐。）

4. 旧直连清理（保持可回退）

现在 recyclables/streamlit 里保留了旧脚本与 repo_legacy.py，短期先别删；等四页 API 化稳定后，再统一打包清理。

5. 小型回归测试单（建议当晚就跑）

检索：中英关键词、限定出处、limit=10/200 边界；长文本高亮是否卡顿。

编辑：批量修改多行后一次提交，核对真正改动的键值；空值与换行的处理。

删除：输入多个 ID（含不存在的 ID），应部分成功、部分失败且有提示。

单条入库：空 src 或空 tgt 的容错策略与原来一致。

批量入库：CSV 列名混搭（src_text/target_text/...）与空行、重复去重是否生效。

批量替换：预览与执行返回的数量一致，大小写/整词/正则三种组合随机抽测。

### 3. Wordloom工具箱开发：
1. 你现行脚本（我只做“壳”整合，不动核心逻辑）

tree.py（或你现用导出目录树脚本）

fix_path.py（最新版：包含“凡不是 ../static 开头就改”的规则）

gif_maker.py（含你现在的 ffmpeg 命令与参数）

2. 一份最小的测试素材包（放进 assets/_samples/，用于做内测按钮）

3–5 个 .md，覆盖：

已经是 ../static/... 的

不是 ../static/... 的（应被替换）

既有 ![]() 又有 []() 的混合

2–3 个媒体文件（.gif / .jpg / .png / .mp4），其中至少 1 个要用到你的路径修复

一个“你觉得正确”的 TREE.md 示例（我对齐生成格式）

3. 你的小偏好（写文本就行，我会固化到默认设置）

path.prefix（默认 ../static ）

tree.ignore 列表（比如 [".git", ".venv", "__pycache__", "node_modules"]）

GIF 转换的默认参数（目标宽度、时长、帧率、是否生成缩略图）

你把这 3 类东西丢给我，我就直接把 GUI 壳接起来，首次交付即是可执行文件 + 源码骨架，并保证和你原有脚本等价、可回退、可单独运行。

### 4. 数据库分批导出：
批次顺序与内容：

B1｜数据库与结构快照（先发这个）

三份库（或其中你确定要合并的那几份）：backend/storage/wordloom.db、backend/storage/app.db、frontend/streamlit/app.db

三份结构快照（若你这边能立即导出更好；不能的话发库也行）：

schema_backend.sql、schema_backend_app.sql、schema_frontend_app.sql（用 .schema 导出即可）

可选：rowcounts.txt（各表 COUNT 统计）

B2｜后端“真相源”定义（模型+Schema+连接）

api/app/models.py、api/app/schemas.py、api/app/database.py、api/app/main.py

api/app/repo.py 与（如果存在）api/core/repo.py

脱敏版 .env.sample（只保留键名与示例值）

B3｜后端路由（写入/批量导入的入口）

api/app/routers/entries.py、api/app/routers/sources.py（以及其他与你入库相关的路由）

B4｜前端与数据层影子

frontend/streamlit/models.py、frontend/streamlit/repo.py、frontend/streamlit/app.py

B5｜关键页面（读写路径验证）

pages/* 里这几份：Home_Admin、From_Page、Insert、Bulk_Insert_plus_status（文件名照你现有的发）

B6｜导入与清洗工具（如有）

import_csv.py、export_csv.py、init_tm_db.py、text_utils.py、样例 my_segments.csv（50–200 行就够）

任何时候你只要把当前批次发过来，我就按该批次做完分析与对齐，再告诉你下一步微调点。这样既不积压，也不丢上下文。

### 5. 前端新增：
M0｜仓库初始化

新建 Next.js（App Router + TS + Tailwind）。

建两组路由分区：(public)、(admin)；加 middleware.ts 预留鉴权钩子。

M1｜公开端雏形（只读，SSG/ISR）

/ 公开首页、/source/[slug] 详情：先假数据→再接 FastAPI /public/*。

generateMetadata 做 SEO/OG。

验收：禁用 JS 也能看到内容、刷新无白屏、分享链接可用。

M2｜后台端 MVP（替代 Streamlit 的 Home/Insert/From/Bulk）

/admin 列表只读 → 行内编辑（PATCH）。

/admin/insert：单条/批量（默认 en→zh、不拆分）。

/admin/from/[sourceId]：顺序浏览 + 中途插入。

验收：编辑自动保存、失败 toast、筛选切换无整页白屏。

M3｜鉴权与安全

FastAPI /auth/login 颁发 JWT；NextAuth（Credentials）或自定义 Session。

middleware.ts 保护 /admin*；可选 IP 白名单。

公开端默认只读、过滤私有字段。

M4｜审计与优化（可选）

审计日志（记录每次改动）。

公共媒体走 CDN；站点加 sitemap/robots。

Emoji

📚 Insert 🛠️ Bulk 📥 Insert 📑FromPage
📝 Log 🏡 Home 🎞️ ShowWhatIHave
<font color="C00000">From now on, we'll have demo! See them below!</font>

Quick Commands from Git
git add CHANGELOG.md
git commit -m "docs: update changelog for v0.4.0"
git tag -a v0.4.0 -m "release 0.4.0"
git push origin v0.4.0

随手提交：
git add -A
git commit -m

| 类型       | 说明           |
| -------- | ------------ |
| feat     | 新功能（feature） |
| fix      | 修bug         |
| refactor | 重构逻辑，不改功能    |
| doc      | 写文档          |
| chore    | 杂项、小维护       |
| style    | 改前端样式        |

# Git Cheat Sheet · Wordloom

## 开工三步
git switch main
git pull --rebase origin main
git switch -c feat/<task-name>   # 动词+主题，如 feat/bulk-insert-ui

## 开发提交流
git status
git add -p         # 选择性暂存（推荐）
git add .          # 全量暂存
git commit -m "feat: <what & why>"
git push -u origin <branch>   # 首次推送建立跟踪

## 合并回主线（推荐线性历史）
# 在功能分支
git fetch origin
git rebase origin/main
# 解决冲突：编辑→git add <file>→git rebase --continue

# 切回主分支并确保最新
git switch main
git pull --rebase origin main
git merge --ff-only <branch>
git push origin main

# 清理
git branch -d <branch>
git push origin --delete <branch>   # 可选，删远端

## 查看与历史
git branch -a
git log --oneline --graph --decorate --all
git show <commit>
git blame <file>

## 暂存（改到一半先收起来）
git stash
git pull --rebase origin main
git stash pop

## 标签（里程碑/发布点）
git tag -a v0.9-bulk -m "Bulk Insert UI overhaul"
git push origin v0.9-bulk

## 常见故障
# 1) cannot pull with rebase: You have unstaged changes
git add . && git commit -m "save work"   # 或 git stash / git restore .
# 2) push 被拒（非快进）
git pull --rebase origin <branch> && git push
# 3) 不小心复制了“Switched to ...”当命令
#   仅输入以 git 开头的命令；那行是提示不是命令。

