import sqlite3
from datetime import datetime

DB = "tm.db"

ddl = """
PRAGMA foreign_keys = ON;

-- 关键表述类型表
CREATE TABLE IF NOT EXISTS types(
    type_code TEXT PRIMARY KEY,
    type_name TEXT,
    parent_code TEXT
);

-- 出处表
CREATE TABLE IF NOT EXISTS sources(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    publisher TEXT,
    year INTEGER,
    url TEXT,
    license TEXT
);

-- 文档表
CREATE TABLE IF NOT EXISTS documents(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    client TEXT,
    version TEXT,
    notes TEXT
);

-- 双语句段表
CREATE TABLE IF NOT EXISTS segments(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    align_id TEXT,
    src_lang TEXT,
    tgt_lang TEXT,
    src_text TEXT,
    tgt_text TEXT,
    type_code TEXT,
    source_id INTEGER,
    doc_id INTEGER,
    quality REAL,
    created_at TEXT,
    updated_at TEXT,
    FOREIGN KEY (type_code) REFERENCES types(type_code),
    FOREIGN KEY (source_id) REFERENCES sources(id),
    FOREIGN KEY (doc_id) REFERENCES documents(id)
);

-- 全文索引 (FTS5)
CREATE VIRTUAL TABLE IF NOT EXISTS segments_fts
USING fts5(src_text, tgt_text, content='segments', content_rowid='id');

-- 触发器保持 FTS5 同步
CREATE TRIGGER IF NOT EXISTS seg_ai AFTER INSERT ON segments BEGIN
  INSERT INTO segments_fts(rowid, src_text, tgt_text)
  VALUES (new.id, new.src_text, new.tgt_text);
END;
CREATE TRIGGER IF NOT EXISTS seg_ad AFTER DELETE ON segments BEGIN
  INSERT INTO segments_fts(segments_fts, rowid, src_text, tgt_text)
  VALUES('delete', old.id, old.src_text, old.tgt_text);
END;
CREATE TRIGGER IF NOT EXISTS seg_au AFTER UPDATE ON segments BEGIN
  INSERT INTO segments_fts(segments_fts, rowid, src_text, tgt_text)
  VALUES('delete', old.id, old.src_text, old.tgt_text);
  INSERT INTO segments_fts(rowid, src_text, tgt_text)
  VALUES (new.id, new.src_text, new.tgt_text);
END;
"""

# 初始化 & 插入样例
con = sqlite3.connect(DB)
cur = con.cursor()
cur.executescript(ddl)

now = datetime.now().isoformat()

# 插入样例类型
types = [
    ("DEF", "定义类", None),
    ("OBL", "义务类", None),
    ("RIGHT", "权利类", None),
    ("COND", "条件类", None),
    ("EXCP", "例外类", None),
    ("TIME", "时限类", None),
]
cur.executemany("INSERT OR IGNORE INTO types(type_code,type_name,parent_code) VALUES (?,?,?)", types)

# 插入样例出处
cur.execute("INSERT INTO sources(title,publisher,year,url,license) VALUES (?,?,?,?,?)",
            ("合同法手册","法律出版社",2020,"http://example.com","© 2020 LegalPub"))

# 插入样例文档
cur.execute("INSERT INTO documents(filename,client,version,notes) VALUES (?,?,?,?)",
            ("contract_v1.docx","ClientA","v1","初稿"))

# 插入样例双语句段
segments = [
    ("A001","en","zh","This Agreement applies to ...","本协议适用于……","DEF",1,1,0.9,now,now),
    ("A002","en","zh","The Supplier shall provide ...","供应商应当提供……","OBL",1,1,0.95,now,now),
    ("A003","en","zh","Except as otherwise provided ...","除非另有规定……","EXCP",1,1,0.85,now,now),
]
cur.executemany("""
INSERT INTO segments(align_id,src_lang,tgt_lang,src_text,tgt_text,type_code,source_id,doc_id,quality,created_at,updated_at)
VALUES (?,?,?,?,?,?,?,?,?,?,?)
""", segments)

con.commit()
con.close()
print("✅ Database initialized with sample data.")
