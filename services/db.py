import sqlite3
import json
from models.schemas import InvestorProfile

DB_PATH = "memory.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Chat history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Investor profile table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS investor_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            investment_interests TEXT,
            preferred_industries TEXT,
            risk_profile TEXT,
            frequently_researched TEXT
        )
    """)
    
    # Seed default profile if not exists
    cursor.execute("SELECT COUNT(*) FROM investor_profile")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO investor_profile (name, investment_interests, preferred_industries, risk_profile, frequently_researched) VALUES (?, ?, ?, ?, ?)",
            ("Valued Client", "Low-risk technology investments", json.dumps(["Technology", "Semiconductors"]), "Moderate", json.dumps([]))
        )
        
    conn.commit()
    conn.close()

def save_chat_message(session_id: str, role: str, content: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_history (session_id, role, content) VALUES (?, ?, ?)",
        (session_id, role, content)
    )
    conn.commit()
    conn.close()

def get_chat_history(session_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content FROM chat_history WHERE session_id = ? ORDER BY id ASC",
        (session_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"role": row[0], "content": row[1]} for row in rows]

def clear_chat_history(session_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()

def get_all_sessions():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT session_id FROM chat_history ORDER BY id DESC")
    sessions = [row[0] for row in cursor.fetchall() if row[0]]
    conn.close()
    return sessions

def get_investor_profile() -> InvestorProfile:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, investment_interests, preferred_industries, risk_profile, frequently_researched FROM investor_profile ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        try:
            pref_ind = json.loads(row[2])
        except Exception:
            pref_ind = []
        try:
            freq_res = json.loads(row[4])
        except Exception:
            freq_res = []
        return InvestorProfile(
            name=row[0],
            investment_interests=row[1],
            preferred_industries=pref_ind,
            risk_profile=row[3],
            frequently_researched=freq_res
        )
    return InvestorProfile()

def update_investor_profile(profile: InvestorProfile):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE investor_profile 
        SET name = ?, investment_interests = ?, preferred_industries = ?, risk_profile = ?, frequently_researched = ?
        WHERE id = 1
    """, (
        profile.name,
        profile.investment_interests,
        json.dumps(profile.preferred_industries),
        profile.risk_profile,
        json.dumps(profile.frequently_researched)
    ))
    conn.commit()
    conn.close()

# Initialize DB on import
init_db()
