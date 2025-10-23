# Orbit (MVP · Streamlit + SQLite)

**功能**：
- Memos：快速记录/筛选/编辑（id, ts, text, tags[], source?, links[], status）
- Tasks：看板式（Todo/Doing/Done 切换）、(id, title, created_at, due_at?, status, effort 1-5, memo_id?)
- Stats：按日/周聚合：memos_count, tasks_done_count, avg_effort（范围：7d/30d）

**本地存储**：`orbit.db`（SQLite）

**运行**
```bash
# 1) 创建虚拟环境（可选）并安装依赖
pip install -r requirements.txt
# 2) 初始化数据库（会生成 orbit.db，并插入少量示例数据）
python init_db.py
# 3) 运行 Streamlit
streamlit run app.py
```

**导入/导出**
- 导出为统一交换格式：`python export_json.py` → 生成 `orbit_export.json`
- 导入 JSON：`python import_json.py orbit_export.json`（将 JSON 写回 SQLite；若 id 冲突则更新，新增则插入）

> 这是一个“运行逻辑骨架”，专注流畅操作：20s 记想法、10s 起任务、1s 切状态，一眼看到今天与本周节奏。
