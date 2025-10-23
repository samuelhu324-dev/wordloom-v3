import sqlite3
import pandas as pd
import sys

DB = "tm.db"

def export_segments(out_path="segments_export.csv"):
    con = sqlite3.connect(DB)

    # 联合 documents 和 sources 一起导出
    query = """
    SELECT s.id, s.align_id, s.src_lang, s.tgt_lang,
           s.src_text, s.tgt_text, s.type_code,
           s.quality, s.created_at, s.updated_at,
           d.filename AS document, d.client AS doc_client,
           so.title AS source_title, so.publisher AS source_publisher, so.year AS source_year
    FROM segments s
    LEFT JOIN documents d ON d.id = s.doc_id
    LEFT JOIN sources so ON so.id = s.source_id
    ORDER BY s.id;
    """

    df = pd.read_sql_query(query, con)
    con.close()

    # 自动根据扩展名选择导出格式
    if out_path.endswith(".xlsx"):
        df.to_excel(out_path, index=False)
    else:
        df.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"✅ Exported {len(df)} rows to {out_path}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        export_segments(sys.argv[1])
    else:
        export_segments()
