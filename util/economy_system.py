# This is the economy system for Palbot.
# Storage is done in a SQLite3 database.

import sqlite3
import os

DATABASE_PATH = os.path.join('data', 'economy.db')

def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_points (
            user_id TEXT PRIMARY KEY,
            user_name TEXT NOT NULL,
            points INTEGER NOT NULL DEFAULT 0,
            steam_id TEXT,
            verification_code TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_invites (
            user_id TEXT PRIMARY KEY,
            user_name TEXT NOTs NULL,
            invite_count INTEGER NOT NULL DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

# Admin Functionality
def add_points(user_id, user_name, points):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_points (user_id, user_name, points)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET points = points + excluded.points, user_name = excluded.user_name;
    ''', (user_id, user_name, points))
    conn.commit()
    conn.close()

def set_points(user_id, user_name, points):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_points (user_id, user_name, points)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET points = excluded.points, user_name = excluded.user_name;
    ''', (user_id, user_name, points))
    conn.commit()
    conn.close()

def get_points(user_id: str, user_name: str) -> tuple:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user_name, points FROM user_points WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()

    if not result:
        cursor.execute('INSERT INTO user_points (user_id, user_name, points) VALUES (?, ?, 0)', (user_id, user_name))
        conn.commit()
        result = (user_name, 0)

    conn.close()
    return result

# For the leaderboard
def get_top_points(limit=10):
    """Retrieve the top users by points."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user_name, points FROM user_points ORDER BY points DESC LIMIT ?', (limit,))
    result = cursor.fetchall()
    conn.close()
    return result

def get_user_rank(user_id):
    """Retrieve the rank of a user by points."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) + 1
        FROM user_points
        WHERE points > (SELECT points FROM user_points WHERE user_id = ?)
    ''', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def link_steam_account(user_id, steam_id, verification_code=None):
    """Link a Steam account to a Discord user."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE user_points SET steam_id = ?, verification_code = ?
        WHERE user_id = ?
    ''', (steam_id, verification_code, user_id))
    conn.commit()
    conn.close()

def get_steam_id(user_id):
    """Retrieve the Steam ID linked to a Discord user."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT steam_id FROM user_points WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# Invites tracking
def add_invite(user_id, user_name):
    """Increment the invite count for a user."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_invites (user_id, user_name, invite_count)
        VALUES (?, ?, 1)
        ON CONFLICT(user_id) DO UPDATE SET invite_count = invite_count + 1, user_name = excluded.user_name;
    ''', (user_id, user_name))
    conn.commit()
    conn.close()

def get_invite_count(user_id):
    """Retrieve the number of accepted invites for a user."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user_name, invite_count FROM user_invites WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result if result else (None, 0)

def get_top_invites(limit=10):
    """Retrieve the top users by invite count."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_name, invite_count FROM user_invites ORDER BY invite_count DESC LIMIT ?
    ''', (limit,))
    result = cursor.fetchall()
    conn.close()
    return result

# Steam Link
async def link_steam_account(user_id, steam_id, verification_code=None):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user_name FROM user_points WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    user_name = result[0] if result else 'Unknown'
    
    cursor.execute('''
        INSERT INTO user_points (user_id, user_name, points, steam_id, verification_code)
        VALUES (?, ?, 0, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET steam_id = excluded.steam_id, verification_code = excluded.verification_code, user_name = CASE WHEN excluded.user_name != 'Unknown' THEN excluded.user_name ELSE user_name END;
    ''', (user_id, user_name, steam_id, verification_code))
    conn.commit()
    conn.close()

async def update_discord_username(user_id, user_name):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE user_points SET user_name = ? WHERE user_id = ?
    ''', (user_name, user_id))
    conn.commit()
    conn.close()