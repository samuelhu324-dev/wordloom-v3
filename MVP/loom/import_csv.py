import sqlite3
import pandas as pd
from datetime import datetime
import sys

DB = "tm.db"

def import_csv(csv_path):
    con = sqlite3.connect(DB)
    cur = con.cursor()

    df = pd.read_csv(csv_path)
    now = datetime.now().isoformat()

    # 插入数据
    for _, row in df.iterrows():
        cur.execute("""
        INSERT INTO segments(
            align_id, src_lang, tgt_lang, src_text, tgt_text,
            type_code, source_id, doc_id, quality, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row.get("align_id"),
            row.get("src_lang","en"),
            row.get("tgt_lang","zh"),
            row.get("src_text"),
            row.get("tgt_text"),
            row.get("type_code"),
            int(row.get("source_id",1)) if not pd.isna(row.get("source_id")) else None,
            int(row.get("doc_id",1)) if not pd.isna(row.get("doc_id")) else None,
            float(row.get("quality",1.0)) if not pd.isna(row.get("quality")) else None,
            now, now
        ))

    con.commit()
    con.close()
    print(f"✅ Imported {len(df)} rows from {csv_path} into {DB}.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python import_csv.py my_segments.csv")
    else:
        import_csv(sys.argv[1])
