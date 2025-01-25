import aiosqlite
import os
import json

DATABASE_PATH = os.path.join('data', 'palbot.db')

async def add_experience(user_id, pal_name, experience_gained):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''UPDATE user_pals SET experience = experience + ? WHERE user_id = ? AND pal_name = ?;''', (experience_gained, user_id, pal_name))
        await db.commit()

async def add_pal(user_id, pal_name, experience=0, level=1):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            INSERT INTO user_pals (user_id, pal_name, experience, level)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, pal_name) DO UPDATE
            SET experience = excluded.experience, level = excluded.level;
        ''', (user_id, pal_name, experience, level))
        await db.commit()

async def get_pals(user_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('''
            SELECT pal_name, level, experience FROM user_pals WHERE user_id = ?
        ''', (user_id,))
        pals = await cursor.fetchall()
        return pals
    
async def level_up(user_id, pal_name):
    # reworked leveling system...
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('''
            SELECT level, experience FROM user_pals
            WHERE user_id = ? AND pal_name = ?;
        ''', (user_id, pal_name))
        pal = await cursor.fetchone()

        if pal:
            level = pal[0]
            experience = pal[1]
            
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
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('''
            SELECT level, experience FROM user_pals
            WHERE user_id = ? AND pal_name = ?;
        ''', (user_id, pal_name))
        return await cursor.fetchone()

async def check_pal(user_id, pal_name):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('''
            SELECT 1 FROM user_pals WHERE user_id = ? AND pal_name = ?
        ''', (user_id, pal_name))
        return await cursor.fetchone() is not None
    
async def get_palgame_settings():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT setting_value FROM economy_settings WHERE setting_key = ?', ('palgame_config',))
        result = await cursor.fetchone()
        if result:
            return json.loads(result[0])
        return {
            "catch_cooldown": 90,
            "catch_reward_min": 10,
            "catch_reward_max": 50,
            "battle_cooldown": 90,
            "battle_reward_min": 20,
            "battle_reward_max": 50,
            "battle_experience": 100,
            "adventure_cooldown": 90,
            "adventure_reward_min": 50,
            "adventure_reward_max": 200,
            "adventure_experience_min": 100,
            "adventure_experience_max": 500
        }

async def update_palgame_settings(new_settings):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT setting_value FROM economy_settings WHERE setting_key = ?', ('palgame_config',))
        result = await cursor.fetchone()
        current_settings = json.loads(result[0]) if result else {}

        current_settings.update(new_settings)

        await db.execute('''
            INSERT INTO economy_settings (setting_key, setting_value)
            VALUES (?, ?)
            ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value;
        ''', ('palgame_config', json.dumps(current_settings)))
        await db.commit()
