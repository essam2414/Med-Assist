import sqlite3
import os

db_path = r"c:\Users\essam\OneDrive\Desktop\FYP\eus328\med-assistant-web\backend\med_assistant.db"

if not os.path.exists(db_path):
    print(f"Error: Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    print("Altering table ai_analytics to add consultation_details...")
    cursor.execute("ALTER TABLE ai_analytics ADD COLUMN consultation_details JSON")
    print("Column consultation_details added.")
except sqlite3.OperationalError as e:
    print(f"Could not add consultation_details: {e}")

try:
    print("Altering table ai_analytics to add patient_names...")
    cursor.execute("ALTER TABLE ai_analytics ADD COLUMN patient_names JSON")
    print("Column patient_names added.")
except sqlite3.OperationalError as e:
    print(f"Could not add patient_names: {e}")

conn.commit()
conn.close()
print("Database schema update finished.")
