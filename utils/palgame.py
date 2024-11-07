import aiosqlite
import os
import psycopg2
from utils.database import CONFIG_PG
import utils.settings as settings

DATABASE_PATH = os.path.join('data', 'palbot.db')

async def add_experience(user_id, pal_name, experience_gained):
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    UPDATE user_pals SET experience = experience + %s 
                    WHERE user_id = %s AND pal_name = %s;
                ''', (experience_gained, user_id, pal_name))
            conn.commit()
        except psycopg2.Error as e:
            print(f"Error adding experience: {e}")
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute('''
                UPDATE user_pals SET experience = experience + ? 
                WHERE user_id = ? AND pal_name = ?;
            ''', (experience_gained, user_id, pal_name))
            await db.commit()

async def add_pal(user_id, pal_name, experience=0, level=1):
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO user_pals (user_id, pal_name, experience, level)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT(user_id, pal_name) DO UPDATE 
                    SET experience = EXCLUDED.experience, level = EXCLUDED.level;
                ''', (user_id, pal_name, experience, level))
            conn.commit()
        except psycopg2.Error as e:
            print(f"Error adding pal: {e}")
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute('''
                INSERT INTO user_pals (user_id, pal_name, experience, level)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, pal_name) DO UPDATE 
                SET experience = excluded.experience, level = excluded.level;
            ''', (user_id, pal_name, experience, level))
            await db.commit()

async def get_pals(user_id):
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    SELECT pal_name, level, experience FROM user_pals 
                    WHERE user_id = %s;
                ''', (user_id,))
                pals = cursor.fetchall()
            return pals
        except psycopg2.Error as e:
            print(f"Error fetching pals: {e}")
            return []
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute('''
                SELECT pal_name, level, experience FROM user_pals 
                WHERE user_id = ?;
            ''', (user_id,))
            pals = await cursor.fetchall()
        return pals
    
async def level_up(user_id, pal_name):
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    SELECT level, experience FROM user_pals 
                    WHERE user_id = %s AND pal_name = %s;
                ''', (user_id, pal_name))
                pal = cursor.fetchone()

                if pal:
                    level, experience = pal
                    required_experience = 1000 + (level - 1) * 200

                    while experience >= required_experience:
                        level += 1
                        experience -= required_experience
                        required_experience = 1000 + (level - 1) * 200

                    cursor.execute('''
                        UPDATE user_pals 
                        SET level = %s, experience = %s 
                        WHERE user_id = %s AND pal_name = %s;
                    ''', (level, experience, user_id, pal_name))
            conn.commit()
        except psycopg2.Error as e:
            print(f"Error leveling up pal: {e}")
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute('''
                SELECT level, experience FROM user_pals 
                WHERE user_id = ? AND pal_name = ?;
            ''', (user_id, pal_name))
            pal = await cursor.fetchone()

            if pal:
                level, experience = pal
                required_experience = 1000 + (level - 1) * 200

                while experience >= required_experience:
                    level += 1
                    experience -= required_experience
                    required_experience = 1000 + (level - 1) * 200

                await db.execute('''
                    UPDATE user_pals 
                    SET level = ?, experience = ? 
                    WHERE user_id = ? AND pal_name = ?;
                ''', (level, experience, user_id, pal_name))
                await db.commit()

async def get_stats(user_id, pal_name):
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    SELECT level, experience FROM user_pals 
                    WHERE user_id = %s AND pal_name = %s;
                ''', (user_id, pal_name))
                return cursor.fetchone()
        except psycopg2.Error as e:
            print(f"Error fetching stats: {e}")
            return None
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute('''
                SELECT level, experience FROM user_pals 
                WHERE user_id = ? AND pal_name = ?;
            ''', (user_id, pal_name))
            return await cursor.fetchone()

async def check_pal(user_id, pal_name):
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    SELECT 1 FROM user_pals 
                    WHERE user_id = %s AND pal_name = %s;
                ''', (user_id, pal_name))
                return cursor.fetchone() is not None
        except psycopg2.Error as e:
            print(f"Error checking pal: {e}")
            return False
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute('''
                SELECT 1 FROM user_pals 
                WHERE user_id = ? AND pal_name = ?;
            ''', (user_id, pal_name))
            return await cursor.fetchone() is not None