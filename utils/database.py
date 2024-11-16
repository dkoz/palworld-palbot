# This is the database system for Palbot.
# Storage is done using aiosqlite.

import aiosqlite
import os
import psycopg2
from urllib.parse import urlparse
from psycopg2 import sql
import utils.settings as settings

DATABASE_PATH = os.path.join('data', 'palbot.db')
CONFIG_PG = ''


async def init_db():
    #Check if the connection string is available
    if settings.connection_string:
        def parse_connection_url(url):
            result = urlparse(url)
            return {
                'user': result.username,
                'password': result.password,
                'host': result.hostname,
                'port': result.port or 5432,  # PostgreSQL default port is 5432
            }

        #Parse the connection string
        conn_params = parse_connection_url(settings.connection_string)

        #Configure connection parameters
        config = {
            'user': conn_params.get('user'),
            'password': conn_params.get('password'),
            'host': conn_params.get('host'),
            'port': conn_params.get('port'),
        }

        #defines the name of the database
        database_name = 'palbot_db' 

        #Connect to PostgreSQL database
        try:
            #First connect to the default database (template1)
            connection = psycopg2.connect(**config, dbname="template1")
            connection.autocommit = True
            cursor = connection.cursor()

            #Check if the database already exists
            cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{database_name}'")
            result = cursor.fetchone()

            if not result:
                cursor.execute(f"CREATE DATABASE {database_name}")
               # print(f"Database '{database_name}' created successfully.")
            #else:
             #   print(f"Database '{database_name}' already exists.")

        except psycopg2.Error as e:
            print(f"Error: {e}")
        finally:
            cursor.close()
            connection.close()

        #Connect to newly created database
        config['dbname'] = database_name

        global CONFIG_PG
        CONFIG_PG = config

        try:
            connection = psycopg2.connect(**CONFIG_PG)
            connection.autocommit = True
            cursor = connection.cursor()

            #Create the tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS servers (
                    guild_id VARCHAR(255) NOT NULL,
                    server_name VARCHAR(255) PRIMARY KEY,
                    server_host VARCHAR(255) NOT NULL,
                    rcon_port VARCHAR(32) NOT NULL,
                    connection_port VARCHAR(32) NOT NULL,
                    admin_pass VARCHAR(255) NOT NULL
                );
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_points (
                    user_id VARCHAR(255) PRIMARY KEY,
                    user_name VARCHAR(255) NOT NULL,
                    points BIGINT NOT NULL DEFAULT 0,
                    steam_id VARCHAR(255),
                    verification_code VARCHAR(255)
                );
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_invites (
                    user_id VARCHAR(255) PRIMARY KEY,
                    user_name VARCHAR(255) NOT NULL,
                    invite_count INT NOT NULL DEFAULT 0
                );
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS economy_settings (
                    setting_key VARCHAR(255) PRIMARY KEY,
                    setting_value VARCHAR(999) NOT NULL
                );
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS server_events (
                    server_name VARCHAR(255) PRIMARY KEY,
                    channel_id VARCHAR(32) NOT NULL
                );
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS server_queries (
                    server_name VARCHAR(255) PRIMARY KEY,
                    channel_id VARCHAR(32) NOT NULL,
                    status_message_id VARCHAR(32),
                    players_message_id VARCHAR(32)
                );
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    steamid VARCHAR(255) PRIMARY KEY,
                    name VARCHAR(255),
                    playeruid VARCHAR(255)
                );
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cooldowns (
                    user_id VARCHAR(255) NOT NULL,
                    command VARCHAR(255) NOT NULL,
                    expires_at VARCHAR(50) NOT NULL,
                    PRIMARY KEY (user_id, command)
                );
            ''')

            # Palgame tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_pals (
                    user_id VARCHAR(255),
                    pal_name VARCHAR(255),
                    experience INT NOT NULL DEFAULT 0,
                    level INT NOT NULL DEFAULT 1,
                    PRIMARY KEY (user_id, pal_name)
                );
            ''')        

            #Enter default settings into the savings system
            default_settings = {
                "currency_name": "Points",
                "invite_reward": "10",
                "work_reward_min": "20",
                "work_reward_max": "50",
                "work_timer": "360",
                "daily_reward": "200",
                "daily_timer": "86400",
                "work_description": '["Your Pals butchered the invaders and earned {earned_points} {currency}!", "Anubis stumbled upon {earned_points} {currency} in the hot tub!"]',
                "role_bonuses": '{"Server Booster": 10, "Supporter": 5}',
                "vote_slug": "",
                "vote_apikey": "",
                "vote_reward": "100"
            }
            for key, value in default_settings.items():
                try:
                    cursor.execute('''
                        INSERT INTO economy_settings (setting_key, setting_value)
                        VALUES (%s, %s)
                        ON CONFLICT (setting_key) DO UPDATE
                        SET setting_value = EXCLUDED.setting_value;
                    ''', (key, value))
                except psycopg2.Error as e:
                    print(f"Error inserting the setting {key}: {e}")

            connection.commit()
            print("PostgreSql database Complete")
        except psycopg2.Error as e:
            print(f"Error connecting to PostgreSQL: {e}")
        finally:
            if connection:
                cursor.close()
                connection.close()



    else:
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
            await db.execute('''
                CREATE TABLE IF NOT EXISTS cooldowns (
                    user_id TEXT NOT NULL,
                    command TEXT NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    PRIMARY KEY (user_id, command)
                ) 
            ''')
            # Palgame tables
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_pals (
                    user_id TEXT NOT NULL,
                    pal_name TEXT NOT NULL,
                    experience INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    PRIMARY KEY (user_id, pal_name)
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
                "daily_timer": "86400",
                "work_description": '["Your Pals butchered the invaders and earned {earned_points} {currency}!", "Anubis stumbled upon {earned_points} {currency} in the hot tub!"]',
                "role_bonuses": '{"Server Booster": 10, "Supporter": 5}',
                "vote_slug": "",
                "vote_apikey": "",
                "vote_reward": "100"
            }
            for key, value in default_settings.items():
                await db.execute('''
                    INSERT INTO economy_settings (setting_key, setting_value)
                    VALUES (?, ?)
                    ON CONFLICT(setting_key) DO NOTHING;
                ''', (key, value))
            await db.commit()
            print("SqlLite database Complete")



# Server Management
async def add_server(guild_id, server_name, server_host, rcon_port, connection_port, admin_pass):
    if settings.connection_string:  
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql.SQL('''
                    INSERT INTO servers (guild_id, server_name, server_host, rcon_port, connection_port, admin_pass)
                    VALUES (%s, %s, %s, %s, %s, %s)
                '''), (guild_id, server_name, server_host, rcon_port, connection_port, admin_pass))
                conn.commit()
        except psycopg2.Error as e:
            print(f"Error inserting server: {e}")
        finally:
            conn.close()
    else:    
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute('''
                INSERT INTO servers (guild_id, server_name, server_host, rcon_port, connection_port, admin_pass)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (guild_id, server_name, server_host, rcon_port, connection_port, admin_pass))
            await db.commit()


async def remove_server(server_name):
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM servers WHERE server_name = %s", (server_name,))
                conn.commit()
                return cursor.rowcount > 0
        except psycopg2.Error as e:
            print(f"Error removing server: {e}")
            return False
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute("DELETE FROM servers WHERE server_name = ?", (server_name,))
            await db.commit()
            return cursor.rowcount > 0
        
async def server_autocomplete():
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT server_name FROM servers")
                servers = cursor.fetchall()
                return [server[0] for server in servers]
        except psycopg2.Error as e:
            print(f"Error fetching server names: {e}")
            return []
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute("SELECT server_name FROM servers")
            servers = await cursor.fetchall()
            return [server[0] for server in servers]


async def get_server_details(server_name):
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT server_host, rcon_port, admin_pass FROM servers WHERE server_name = %s', (server_name,))
                result = cursor.fetchone()
                return result
        except psycopg2.Error as e:
            print(f"Error fetching server details: {e}")
            return None
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute('SELECT server_host, rcon_port, admin_pass FROM servers WHERE server_name = ?', (server_name,))
            result = await cursor.fetchone()
            return result    

    
async def edit_server_details(server_name):
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT server_host, rcon_port, connection_port, admin_pass FROM servers WHERE server_name = %s', (server_name,))
                result = cursor.fetchone()
                return result
        except psycopg2.Error as e:
            print(f"Error fetching server details: {e}")
            return None
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute('SELECT server_host, rcon_port, connection_port, admin_pass FROM servers WHERE server_name = ?', (server_name,))
            result = await cursor.fetchone()
            return result
    
async def update_server_details(old_server_name, new_server_name, server_host, rcon_port, connection_port, admin_pass):
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    UPDATE servers 
                    SET server_name = %s, server_host = %s, rcon_port = %s, connection_port = %s, admin_pass = %s 
                    WHERE server_name = %s
                ''', (new_server_name, server_host, rcon_port, connection_port, admin_pass, old_server_name))
                conn.commit()
        except psycopg2.Error as e:
            print(f"Error updating server details: {e}")
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute('''
                UPDATE servers 
                SET server_name = ?, server_host = ?, rcon_port = ?, connection_port = ?, admin_pass = ? 
                WHERE server_name = ?
            ''', (new_server_name, server_host, rcon_port, connection_port, admin_pass, old_server_name))
            await db.commit()
    

async def get_connection_port(server_name):
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT connection_port FROM servers WHERE server_name = %s', (server_name,))
                result = cursor.fetchone()
                return result[0] if result else None
        except psycopg2.Error as e:
            print(f"Error fetching connection port: {e}")
            return None
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute('SELECT connection_port FROM servers WHERE server_name = ?', (server_name,))
            result = await cursor.fetchone()
            return result[0] if result else None


# Admin Functionality
async def add_points(user_id, user_name, points):
    if points < 0:
        raise ValueError("Points to add cannot be negative.")

    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO user_points (user_id, user_name, points)
                    VALUES (%s, %s, %s)
                    ON CONFLICT(user_id) DO UPDATE 
                    SET points = user_points.points + excluded.points, user_name = excluded.user_name;
                ''', (user_id, user_name, points))
            conn.commit()
        except psycopg2.Error as e:
            print(f"Error adding points: {e}")
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute('''
                INSERT INTO user_points (user_id, user_name, points)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET points = points + excluded.points, user_name = excluded.user_name;
            ''', (user_id, user_name, points))
            await db.commit()


async def set_points(user_id, user_name, points):
    if points < 0:
        points = 0

    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO user_points (user_id, user_name, points)
                    VALUES (%s, %s, %s)
                    ON CONFLICT(user_id) DO UPDATE SET points = excluded.points, user_name = excluded.user_name;
                ''', (user_id, user_name, points))
            conn.commit()
        except psycopg2.Error as e:
            print(f"Error setting points: {e}")
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute('''
                INSERT INTO user_points (user_id, user_name, points)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET points = excluded.points, user_name = excluded.user_name;
            ''', (user_id, user_name, points))
            await db.commit()

async def get_points(user_id: str, user_name: str) -> tuple:
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT user_name, points FROM user_points WHERE user_id = %s', (user_id,))
                result = cursor.fetchone()

                if not result:
                    cursor.execute('INSERT INTO user_points (user_id, user_name, points) VALUES (%s, %s, 0)', (user_id, user_name))
                    conn.commit()
                    result = (user_name, 0)

                return result
        except psycopg2.Error as e:
            print(f"Error fetching points: {e}")
            return (None, 0)
        finally:
            conn.close()
    else:
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
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT user_name, points FROM user_points ORDER BY points DESC LIMIT %s', (limit,))
                result = cursor.fetchall()
                return result
        except psycopg2.Error as e:
            print(f"Error fetching top points: {e}")
            return []
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute('SELECT user_name, points FROM user_points ORDER BY points DESC LIMIT ?', (limit,))
            result = await cursor.fetchall()
            return result


async def get_user_rank(user_id):
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    SELECT COUNT(*) + 1
                    FROM user_points
                    WHERE points > (SELECT points FROM user_points WHERE user_id = %s)
                ''', (user_id,))
                result = cursor.fetchone()
                return result[0] if result else 0
        except psycopg2.Error as e:
            print(f"Error fetching user rank: {e}")
            return 0
        finally:
            conn.close()
    else:
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
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    UPDATE user_points SET steam_id = %s, verification_code = %s
                    WHERE user_id = %s
                ''', (steam_id, verification_code, user_id))
                conn.commit()
        except psycopg2.Error as e:
            print(f"Error linking Steam account: {e}")
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute('''
                UPDATE user_points SET steam_id = ?, verification_code = ?
                WHERE user_id = ?
            ''', (steam_id, verification_code, user_id))
            await db.commit()

async def get_steam_id(user_id):
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT steam_id FROM user_points WHERE user_id = %s', (user_id,))
                result = cursor.fetchone()
                return result[0] if result else None
        except psycopg2.Error as e:
            print(f"Error fetching Steam ID: {e}")
            return None
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute('SELECT steam_id FROM user_points WHERE user_id = ?', (user_id,))
            result = await cursor.fetchone()
            return result[0] if result else None

# Invites tracking
async def add_invite(user_id, user_name):
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO user_invites (user_id, user_name, invite_count)
                    VALUES (%s, %s, 1)
                    ON CONFLICT(user_id) DO UPDATE SET invite_count = invite_count + 1, user_name = excluded.user_name;
                ''', (user_id, user_name))
                conn.commit()
        except psycopg2.Error as e:
            print(f"Error adding invite: {e}")
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute('''
                INSERT INTO user_invites (user_id, user_name, invite_count)
                VALUES (?, ?, 1)
                ON CONFLICT(user_id) DO UPDATE SET invite_count = invite_count + 1, user_name = excluded.user_name;
            ''', (user_id, user_name))
            await db.commit()


async def get_invite_count(user_id):
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT user_name, invite_count FROM user_invites WHERE user_id = %s', (user_id,))
                result = cursor.fetchone()
                return result if result else (None, 0)
        except psycopg2.Error as e:
            print(f"Error fetching invite count: {e}")
            return (None, 0)
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute('SELECT user_name, invite_count FROM user_invites WHERE user_id = ?', (user_id,))
            result = await cursor.fetchone()
            return result if result else (None, 0)

async def get_top_invites(limit=10):
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    SELECT user_name, invite_count FROM user_invites ORDER BY invite_count DESC LIMIT %s
                ''', (limit,))
                result = cursor.fetchall()
                return result
        except psycopg2.Error as e:
            print(f"Error fetching top invites: {e}")
            return []
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute('''
                SELECT user_name, invite_count FROM user_invites ORDER BY invite_count DESC LIMIT ?
            ''', (limit,))
            result = await cursor.fetchall()
            return result

async def update_discord_username(user_id, user_name):
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    UPDATE user_points SET user_name = %s WHERE user_id = %s
                ''', (user_name, user_id))
                conn.commit()
        except psycopg2.Error as e:
            print(f"Error updating Discord username: {e}")
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute('''
                UPDATE user_points SET user_name = ? WHERE user_id = ?
            ''', (user_name, user_id))
            await db.commit()

# Economy Settings
async def update_economy_setting(key, value):
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO economy_settings (setting_key, setting_value)
                    VALUES (%s, %s)
                    ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value
                ''', (key, value))
                conn.commit()
        except psycopg2.Error as e:
            print(f"Error updating economy setting: {e}")
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute('''
                INSERT INTO economy_settings (setting_key, setting_value)
                VALUES (?, ?)
                ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value
            ''', (key, value))
            await db.commit()
        
async def get_economy_setting(key):
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT setting_value FROM economy_settings WHERE setting_key = %s', (key,))
                result = cursor.fetchone()
                return result[0] if result else None
        except psycopg2.Error as e:
            print(f"Error fetching economy setting: {e}")
            return None
        finally:
            conn.close()
    else:
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
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO server_events (server_name, channel_id)
                    VALUES (%s, %s)
                    ON CONFLICT(server_name) DO UPDATE SET channel_id = excluded.channel_id;
                ''', (server_name, channel_id))
                conn.commit()
                return True
        except psycopg2.Error as e:
            print(f"Error adding event channel: {e}")
            return False
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute('''
                INSERT INTO server_events (server_name, channel_id)
                VALUES (?, ?)
                ON CONFLICT(server_name) DO UPDATE SET channel_id = excluded.channel_id;
            ''', (server_name, channel_id))
            await db.commit()
            return True

async def remove_event_channel(server_name):
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM server_events WHERE server_name = %s", (server_name,))
                conn.commit()
                return cursor.rowcount > 0
        except psycopg2.Error as e:
            print(f"Error removing event channel: {e}")
            return False
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute("DELETE FROM server_events WHERE server_name = ?", (server_name,))
            await db.commit()
            return cursor.rowcount > 0

async def get_event_channel(server_name):
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT channel_id FROM server_events WHERE server_name = %s', (server_name,))
                result = cursor.fetchone()
                return result[0] if result else None
        except psycopg2.Error as e:
            print(f"Error fetching event channel: {e}")
            return None
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute('SELECT channel_id FROM server_events WHERE server_name = ?', (server_name,))
            result = await cursor.fetchone()
            return result[0] if result else None
    
# Server Query
async def add_query_channel(server_name, channel_id, status_message_id, players_message_id):
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO server_queries (server_name, channel_id, status_message_id, players_message_id)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT(server_name) DO UPDATE SET channel_id = excluded.channel_id, status_message_id = excluded.status_message_id, players_message_id = excluded.players_message_id;
                ''', (server_name, channel_id, status_message_id, players_message_id))
                conn.commit()
                return True
        except psycopg2.Error as e:
            print(f"Error adding query channel: {e}")
            return False
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute('''
                INSERT INTO server_queries (server_name, channel_id, status_message_id, players_message_id)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(server_name) DO UPDATE SET channel_id = excluded.channel_id, status_message_id = excluded.status_message_id, players_message_id = excluded.players_message_id;
            ''', (server_name, channel_id, status_message_id, players_message_id))
            await db.commit()
            return True

async def remove_query_channel(server_name):
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM server_queries WHERE server_name = %s", (server_name,))
                conn.commit()
                return cursor.rowcount > 0
        except psycopg2.Error as e:
            print(f"Error removing query channel: {e}")
            return False
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute("DELETE FROM server_queries WHERE server_name = ?", (server_name,))
            await db.commit()
            return cursor.rowcount > 0

async def get_query_channel(server_name):
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT channel_id, status_message_id, players_message_id FROM server_queries WHERE server_name = %s', (server_name,))
                result = cursor.fetchone()
                return result if result else (None, None, None)
        except psycopg2.Error as e:
            print(f"Error fetching query channel: {e}")
            return (None, None, None)
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute('SELECT channel_id, status_message_id, players_message_id FROM server_queries WHERE server_name = ?', (server_name,))
            result = await cursor.fetchone()
            return result if result else (None, None, None)
    
# Player Logging
async def insert_player_data(steamid, name, playeruid):
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO players (steamid, name, playeruid)
                    VALUES (%s, %s, %s)
                    ON CONFLICT(steamid) DO UPDATE SET
                    name=excluded.name, playeruid=excluded.playeruid
                ''', (steamid, name, playeruid))
                conn.commit()
        except psycopg2.Error as e:
            print(f"Error inserting player data: {e}")
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute('''
                INSERT INTO players (steamid, name, playeruid)
                VALUES (?, ?, ?)
                ON CONFLICT(steamid) DO UPDATE SET
                name=excluded.name, playeruid=excluded.playeruid
            ''', (steamid, name, playeruid))
            await db.commit()

async def get_player_steamids(current: str):
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT steamid FROM players WHERE steamid LIKE %s", (f'%{current}%',))
                steamids = cursor.fetchall()
                return [row[0] for row in steamids]
        except psycopg2.Error as e:
            print(f"Error fetching player steam IDs: {e}")
            return []
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute("SELECT steamid FROM players WHERE steamid LIKE ?", (f'%{current}%',))
            steamids = await cursor.fetchall()
            return [row[0] for row in steamids]

async def get_player_names(current: str):
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT name FROM players WHERE name LIKE %s", (f'%{current}%',))
                names = cursor.fetchall()
                return [row[0] for row in names]
        except psycopg2.Error as e:
            print(f"Error fetching player names: {e}")
            return []
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute("SELECT name FROM players WHERE name LIKE ?", (f'%{current}%',))
            names = await cursor.fetchall()
            return [row[0] for row in names]

async def get_player_profile(identifier: str):
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    SELECT steamid, name, playeruid 
                    FROM players 
                    WHERE steamid = %s OR name = %s
                ''', (identifier, identifier))
                return cursor.fetchone()
        except psycopg2.Error as e:
            print(f"Error fetching player profile: {e}")
            return None
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute('''
                SELECT steamid, name, playeruid 
                FROM players 
                WHERE steamid = ? OR name = ?
            ''', (identifier, identifier))
            return await cursor.fetchone()

# Cooldown tracking for economy commands
# Will implement to Pal Game later on.
async def set_cooldown(user_id, command, expires_at):
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO cooldowns (user_id, command, expires_at)
                    VALUES (%s, %s, %s)
                    ON CONFLICT(user_id, command) DO UPDATE SET expires_at = excluded.expires_at;
                ''', (user_id, command, expires_at))
                conn.commit()
        except psycopg2.Error as e:
            print(f"Error setting cooldown: {e}")
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute('''
                INSERT INTO cooldowns (user_id, command, expires_at)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, command) DO UPDATE SET expires_at = excluded.expires_at;
            ''', (user_id, command, expires_at))
            await db.commit()

async def get_cooldown(user_id, command):
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT expires_at FROM cooldowns WHERE user_id = %s AND command = %s', (user_id, command))
                result = cursor.fetchone()
                return result[0] if result else None
        except psycopg2.Error as e:
            print(f"Error fetching cooldown: {e}")
            return None
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute('SELECT expires_at FROM cooldowns WHERE user_id = ? AND command = ?', (user_id, command))
            result = await cursor.fetchone()
            return result[0] if result else None

async def clear_expired_cooldowns():
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM cooldowns WHERE expires_at::timestamp < NOW()")
                conn.commit()
        except psycopg2.Error as e:
            print(f"Error clearing expired cooldowns: {e}")
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("DELETE FROM cooldowns WHERE expires_at < datetime('now')")
            await db.commit()