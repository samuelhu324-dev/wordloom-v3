需要你先预制一套“可公开的 Demo 数据/模板”，然后再决定用哪种方式（dump 或 seed）固化下来。否则每次录制都要临时造数据，且内容不一致，GIF 很难连贯。

建议你预制的 Demo 模板覆盖哪些内容（最小可用）
1 个 Library
1 个 Bookshelf
2–3 本 Book
Getting Started（教用户怎么创建块/怎么用）
Demo: Tags & Search（用来演示检索）
（可选）Translation Playground（如果翻译是卖点）
20–40 个 Blocks（要让滚动、折叠、跳转看起来“像真的在用”）
5–10 个 Tags（保证搜索/筛选有结果）
Basement：准备 1–2 个“可删除并恢复”的对象（录 Basement GIF 用）
插图/封面要不要？
README/GIF 演示：建议用少量、可复用的公共素材（或你自己画的简单图），避免版权风险。
应用内 Demo 内容：可以放占位图（例如 1–2 张），但不要塞太多；重点还是交互流程。
如果你没有现成插图：优先用纯文本 + 少量图标/emoji就够，保证干净一致。
用 dump 还是 seed？
先做 Demo 模板 → 用 pg_dump 导出 demo_seed.sql（最快、最少改代码，适合你现在要录 GIF）
等项目稳定后，再考虑做 seed 脚本（可控、可幂等、可按版本演进）
推荐工作流（你现在就能做）
docker compose down -v && up -d --build 得到干净环境
通过 UI 手工建好 Demo 模板（一次性）
pg_dump 导出成 demo_seed.sql 并提交到仓库（或放到 assets/demo/）
以后录制前：重置 → 迁移 → 导入 demo_seed.sql
如果你希望我“在 frontend/backend 里翻”现成的导入能力：把你的仓库里 docker-compose.yml、.env.docker.example、以及是否已有 seed/fixtures/import 相关目录（文件名即可）发我，我再给你一个完全贴合当前项目的落地方案。