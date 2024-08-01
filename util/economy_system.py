# This is the economy system for Palbot.
# Storage is done in a SQLite3 database.

import aiosqlite
import os

DATABASE_PATH = os.path.join('data', 'economy.db')

async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_points (
                user_id TEXT PRIMARY KEY,
                user_name TEXT NOT NULL,
                points INTEGER NOT NULL DEFAULT 0,
                steam_id TEXT,
                verification_code TEXT
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_invites (
                user_id TEXT PRIMARY KEY,
                user_name TEXT NOT NULL,
                invite_count INTEGER NOT NULL DEFAULT 0
            )
        ''')
        await db.commit()

# Admin Functionality
async def add_points(user_id, user_name, points):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            INSERT INTO user_points (user_id, user_name, points)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET points = points + excluded.points, user_name = excluded.user_name;
        ''', (user_id, user_name, points))
        await db.commit()

async def set_points(user_id, user_name, points):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            INSERT INTO user_points (user_id, user_name, points)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET points = excluded.points, user_name = excluded.user_name;
        ''', (user_id, user_name, points))
        await db.commit()

async def get_points(user_id: str, user_name: str) -> tuple:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT user_name, points FROM user_points WHERE user_id = ?', (user_id,))
        result = await cursor.fetchone()

        if not result:
            await db.execute('INSERT INTO user_points (user_id, user_name, points) VALUES (?, ?, 0)', (user_id, user_name))
            await db.commit()
            result = (user_name, 0)

        return result

# For the leaderboard
async def get_top_points(limit=10):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT user_name, points FROM user_points ORDER BY points DESC LIMIT ?', (limit,))
        result = await cursor.fetchall()
        return result

async def get_user_rank(user_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('''
            SELECT COUNT(*) + 1
            FROM user_points
            WHERE points > (SELECT points FROM user_points WHERE user_id = ?)
        ''', (user_id,))
        result = await cursor.fetchone()
        return result[0] if result else 0

# Steam Link
async def link_steam_account(user_id, steam_id, verification_code=None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            UPDATE user_points SET steam_id = ?, verification_code = ?
            WHERE user_id = ?
        ''', (steam_id, verification_code, user_id))
        await db.commit()

async def get_steam_id(user_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT steam_id FROM user_points WHERE user_id = ?', (user_id,))
        result = await cursor.fetchone()
        return result[0] if result else None

# Invites tracking
async def add_invite(user_id, user_name):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            INSERT INTO user_invites (user_id, user_name, invite_count)
            VALUES (?, ?, 1)
            ON CONFLICT(user_id) DO UPDATE SET invite_count = invite_count + 1, user_name = excluded.user_name;
        ''', (user_id, user_name))
        await db.commit()

async def get_invite_count(user_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT user_name, invite_count FROM user_invites WHERE user_id = ?', (user_id,))
        result = await cursor.fetchone()
        return result if result else (None, 0)

async def get_top_invites(limit=10):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('''
            SELECT user_name, invite_count FROM user_invites ORDER BY invite_count DESC LIMIT ?
        ''', (limit,))
        result = await cursor.fetchall()
        return result

async def update_discord_username(user_id, user_name):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            UPDATE user_points SET user_name = ? WHERE user_id = ?
        ''', (user_name, user_id))
        await db.commit()
