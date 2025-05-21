import sqlite3

from typing import Any, Dict, List

# Database Setup
def init_db():
    conn = sqlite3.connect("chatbot.db")
    c = conn.cursor()

    # Create the conversation table
    c.execute('''
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    summary TEXT
)
''')
    
    # Create message table
    c.execute('''
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER,
    role TEXT NOT NULL, 
    content TEXT NOT NULL,
    timestamp DATETIME DEAFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES converatsations (id)
)
''')
    
    conn.commit()
    conn.close()


def store_message(session_id:str, role:str, content:str) -> None:
    conn = sqlite3.connect("chatbot.db")
    c = conn.cursor()

    # Get current converstaion id or create a new one
    c.execute("SELECT id FROM conversations WHERE session_id= ? ORDER BY timestamp DESC LIMIT 1", (session_id,))
    result = c.fetchone()

    if result is None:
        # Vreate new conversation
        c.execute("INSERT INTO conversations (session_id) VALUES (?)", (session_id,))
        conversation_id = c.lastrowid
    else:
        conversation_id = result[0]

    # Store mesage
    c.execute("INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
    (conversation_id, role, content))

    conn.commit()
    conn.close()


def get_recent_conversations(session_id:str, limit:int=5) -> List[Dict[str, Any]]:
    conn = sqlite3.connect("chatbot.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Get the recent conversation id
    c.execute('''
SELECT id, timestamp FROM conversations
WHERE session_id = ?
ORDER BY timestamp DESC LIMIT ?
''', (session_id, limit))
    
    converstaions = []

    for conv_row in c. fetchall():
        conv_id = conv_row['id']

        # Get messsages from his coversations
        c.execute('''
SELECT role, content FROM messages
WHERE conversation_id = ?
ORDER BY timestamp ASC
''', (conv_id,))
        
        messages = []

        for msg in c.fetchall():
            messages.append({
            "role": msg["role"],
                "content": msg["content"]
            })
                
            converstaions.append({
                "id": conv_id,
                "timestamp": conv_row["timestamp"],
                "messages": messages
        })
        
    conn.close()
    return converstaions


def start_conversations_summary(session_id:str, conv_id:int, summary:str) -> None:
    conn = sqlite3.connect("chatbot.db")
    c = conn.cursor()
    c.execute("UPDATE conversations SET summary = ? WHERE id = ?", (summary, conv_id))
    conn.commit()
    conn.close()