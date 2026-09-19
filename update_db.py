import mysql.connector

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="newpassword",
        database="crime_management"
    )
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE users ADD COLUMN post VARCHAR(100) DEFAULT 'Inspector'")
    cursor.execute("ALTER TABLE users ADD COLUMN specialization VARCHAR(100) DEFAULT 'General Crime'")
    conn.commit()
    print("Database updated!")
except Exception as e:
    print("Error:", e)
finally:
    if 'conn' in locals() and conn.is_connected():
        cursor.close()
        conn.close()
