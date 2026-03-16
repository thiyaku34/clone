import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

# Users table
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

# Messages table
c.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender TEXT NOT NULL,
    receiver TEXT NOT NULL,
    message TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# Predefined users
sample_users = [
    ("thiyaku", "thiyaku123"),
    ("nandhini", "nandhini123"),

]

for username, password in sample_users:
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    except sqlite3.IntegrityError:
        pass

conn.commit()
conn.close()
print("✅ database.db created with predefined users")