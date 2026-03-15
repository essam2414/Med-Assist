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

        # Check users table for specialty
        cursor.execute("PRAGMA table_info(users)")
        user_columns = [column[1] for column in cursor.fetchall()]
        if "specialty" not in user_columns:
            print("Adding specialty column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN specialty TEXT")
            conn.commit()
            print("Migration successful.")
        else:
            print("Column specialty already exists.")

        # Check consultations table for about
        if "about" not in columns:
            print("Adding about column to consultations table...")
            cursor.execute("ALTER TABLE consultations ADD COLUMN about TEXT")
            conn.commit()
            print("Migration successful.")
        else:
            print("Column about already exists.")
            
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
