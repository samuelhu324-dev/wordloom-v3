#!/usr/bin/env python
"""
直接执行 SQL 迁移：为 orbit_notes 表添加封面图字段
"""
import psycopg2

# 直接指定数据库连接参数
conn = psycopg2.connect(
    host="127.0.0.1",
    port=5433,
    user="postgres",
    password="pgpass",
    database="wordloomorbit"
)

cursor = conn.cursor()

try:
    # 添加 cover_image_url 字段
    cursor.execute('''
        ALTER TABLE orbit_notes
        ADD COLUMN IF NOT EXISTS cover_image_url TEXT NULL
    ''')
    print('✓ Added cover_image_url column')

    # 添加 cover_image_display_width 字段
    cursor.execute('''
        ALTER TABLE orbit_notes
        ADD COLUMN IF NOT EXISTS cover_image_display_width INTEGER NOT NULL DEFAULT 200
    ''')
    print('✓ Added cover_image_display_width column')

    conn.commit()
    print('✓ Database migration completed successfully')

except psycopg2.Error as e:
    conn.rollback()
    print(f'✗ Database error: {e}')
except Exception as e:
    conn.rollback()
    print(f'✗ Error: {e}')
finally:
    cursor.close()
    conn.close()
