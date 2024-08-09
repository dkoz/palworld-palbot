# This is the economy system for Palbot.
# Storage is done using aiosqlite.

import aiosqlite
import os

DATABASE_PATH = os.path.join('data', 'palbot.db')

async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS servers (
                guild_id TEXT NOT NULL,
                server_name TEXT PRIMARY KEY,
                server_host TEXT NOT NULL,
                rcon_port INTEGER NOT NULL,
                connection_port INTEGER NOT NULL,
                admin_pass TEXT NOT NULL
            )
        ''')
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
        await db.execute('''
            CREATE TABLE IF NOT EXISTS economy_settings (
                setting_key TEXT PRIMARY KEY,
                setting_value TEXT NOT NULL
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS server_events (
                server_name TEXT PRIMARY KEY,
                channel_id INTEGER NOT NULL
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS server_queries (
                server_name TEXT PRIMARY KEY,
                channel_id INTEGER NOT NULL,
                status_message_id INTEGER,
                players_message_id INTEGER
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS players (
                steamid TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                playeruid TEXT NOT NULL
            )
        ''')
        # Settings for the economy system
        default_settings = {
            "currency_name": "Points",
            "invite_reward": "10",
            "work_reward_min": "20",
            "work_reward_max": "50",
            "work_timer": "360",
            "daily_reward": "200",
            "daily_timer": "86400"
        }
        for key, value in default_settings.items():
            await db.execute('''
                INSERT INTO economy_settings (setting_key, setting_value)
                VALUES (?, ?)
                ON CONFLICT(setting_key) DO NOTHING;
            ''', (key, value))
        await db.commit()

# Server Management
async def add_server(guild_id, server_name, server_host, rcon_port, connection_port, admin_pass):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            INSERT INTO servers (guild_id, server_name, server_host, rcon_port, connection_port, admin_pass)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (guild_id, server_name, server_host, rcon_port, connection_port, admin_pass))
        await db.commit()
        
async def remove_server(server_name):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("DELETE FROM servers WHERE server_name = ?", (server_name,))
        await db.commit()
        return cursor.rowcount > 0
    
async def server_autocomplete():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("SELECT server_name FROM servers")
        servers = await cursor.fetchall()
        return [server[0] for server in servers]
    
async def get_server_details(server_name):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT server_host, rcon_port, admin_pass FROM servers WHERE server_name = ?', (server_name,))
        result = await cursor.fetchone()
        return result

async def get_connection_port(server_name):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT connection_port FROM servers WHERE server_name = ?', (server_name,))
        result = await cursor.fetchone()
        return result[0] if result else None

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

# Economy Settings
async def update_economy_setting(key, value):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            INSERT INTO economy_settings (setting_key, setting_value)
            VALUES (?, ?)
            ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value
        ''', (key, value))
        await db.commit()
        
async def get_economy_setting(key):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT setting_value FROM economy_settings WHERE setting_key = ?', (key,))
        result = await cursor.fetchone()
        return result[0] if result else None

async def reset_economy_settings():
    await update_economy_setting("currency_name", "Points")
    await update_economy_setting("invite_reward", "10")
    await update_economy_setting("work_reward_min", "20")
    await update_economy_setting("work_reward_max", "50")
    await update_economy_setting("work_timer", "360")
    await update_economy_setting("daily_reward", "200")
    await update_economy_setting("daily_timer", "86400")
    
# Server Events
async def add_event_channel(server_name, channel_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            INSERT INTO server_events (server_name, channel_id)
            VALUES (?, ?)
            ON CONFLICT(server_name) DO UPDATE SET channel_id = excluded.channel_id;
        ''', (server_name, channel_id))
        await db.commit()
        return True

async def remove_event_channel(server_name):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("DELETE FROM server_events WHERE server_name = ?", (server_name,))
        await db.commit()
        return cursor.rowcount > 0

async def get_event_channel(server_name):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT channel_id FROM server_events WHERE server_name = ?', (server_name,))
        result = await cursor.fetchone()
        return result[0] if result else None
    
# Server Query
async def add_query_channel(server_name, channel_id, status_message_id, players_message_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            INSERT INTO server_queries (server_name, channel_id, status_message_id, players_message_id)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(server_name) DO UPDATE SET channel_id = excluded.channel_id, status_message_id = excluded.status_message_id, players_message_id = excluded.players_message_id;
        ''', (server_name, channel_id, status_message_id, players_message_id))
        await db.commit()
        return True

async def remove_query_channel(server_name):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("DELETE FROM server_queries WHERE server_name = ?", (server_name,))
        await db.commit()
        return cursor.rowcount > 0

async def get_query_channel(server_name):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT channel_id, status_message_id, players_message_id FROM server_queries WHERE server_name = ?', (server_name,))
        result = await cursor.fetchone()
        return result if result else (None, None, None)
    
# Player Logging
async def insert_player_data(steamid, name, playeruid):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            INSERT INTO players (steamid, name, playeruid)
            VALUES (?, ?, ?)
            ON CONFLICT(steamid) DO UPDATE SET
            name=excluded.name, playeruid=excluded.playeruid
        ''', (steamid, name, playeruid))
        await db.commit()

async def get_player_steamids(current: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("SELECT steamid FROM players WHERE steamid LIKE ?", (f'%{current}%',))
        steamids = await cursor.fetchall()
        return [row[0] for row in steamids]

async def get_player_names(current: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("SELECT name FROM players WHERE name LIKE ?", (f'%{current}%',))
        names = await cursor.fetchall()
        return [row[0] for row in names]

async def get_player_profile(identifier: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('''
            SELECT steamid, name, playeruid 
            FROM players 
            WHERE steamid = ? OR name = ?
        ''', (identifier, identifier))
        return await cursor.fetchone()
