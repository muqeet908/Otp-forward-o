import sqlite3

db = sqlite3.connect("database.db", check_same_thread=False)

cursor = db.cursor()

# ============================================
# USERS TABLE
# ============================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(

    user_id INTEGER PRIMARY KEY,

    name TEXT,

    username TEXT,

    balance REAL DEFAULT 0,

    total_numbers INTEGER DEFAULT 0,

    total_otps INTEGER DEFAULT 0,

    wallet TEXT
)
""")

# ============================================
# RANGES TABLE
# ============================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS ranges(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    range_text TEXT UNIQUE
)
""")

# ============================================
# NUMBERS TABLE
# ============================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS numbers(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER,

    number_id TEXT,

    number TEXT,

    range_text TEXT,

    otp_received INTEGER DEFAULT 0
)
""")

db.commit()

print("✅ DATABASE READY")
