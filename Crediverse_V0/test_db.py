import pymysql

try:
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="Sarbajit@2025",  # <-- put your real password in quotes
        db="cv"
    )
    print("✅ Connected to MySQL successfully!")
    conn.close()
except Exception as e:
    print("❌ Error:", e)
