import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "agriagent.db")

def init_db():
    """Create tables if they don't exist — call this once at startup"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_state (
            farmer_number TEXT PRIMARY KEY,
            language TEXT DEFAULT 'hi',
            last_response TEXT DEFAULT '',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")


def get_language(farmer_number: str) -> str:
    """Get farmer's last known language, default 'hi'"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT language FROM user_state WHERE farmer_number = ?", (farmer_number,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "hi"


def set_language(farmer_number: str, language: str):
    """Save/update farmer's language preference"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_state (farmer_number, language, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(farmer_number) DO UPDATE SET 
            language = excluded.language,
            updated_at = CURRENT_TIMESTAMP
    """, (farmer_number, language))
    conn.commit()
    conn.close()


def get_last_response(farmer_number: str) -> str:
    """Get farmer's last AI response, for conversational follow-ups"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT last_response FROM user_state WHERE farmer_number = ?", (farmer_number,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else ""


def set_last_response(farmer_number: str, response: str):
    """Save the last AI response for this farmer (for follow-up context)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_state (farmer_number, last_response, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(farmer_number) DO UPDATE SET 
            last_response = excluded.last_response,
            updated_at = CURRENT_TIMESTAMP
    """, (farmer_number, response))
    conn.commit()
    conn.close()