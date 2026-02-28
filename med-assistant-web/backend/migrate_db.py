import sqlite3
import os

db_path = "c:\\Users\\essam\\OneDrive\\Desktop\\FYP\\eus328\\med-assistant-web\\backend\\med_assistant.db"

def migrate():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(consultations)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "recall_bot_id" not in columns:
            print("Adding recall_bot_id column to consultations table...")
            cursor.execute("ALTER TABLE consultations ADD COLUMN recall_bot_id TEXT")
            conn.commit()
            print("Migration successful.")
        else:
            print("Column recall_bot_id already exists.")
            
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
