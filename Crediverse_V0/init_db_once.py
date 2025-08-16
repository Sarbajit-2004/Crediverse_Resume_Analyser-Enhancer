import pymysql

conn = pymysql.connect(host="localhost", user="root", password="Sarbajit@2025")  # <-- your real pwd
with conn.cursor() as cur:
    cur.execute("CREATE DATABASE IF NOT EXISTS cv CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
conn.close()
print("✅ Database 'cv' ensured.")
