import sqlite3

def init_db():
    conn = sqlite3.connect("mock_interview.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        question TEXT,
        answer TEXT,
        grammar INTEGER,
        fluency INTEGER,
        clarity INTEGER,
        feedback TEXT
    )
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized ✅")