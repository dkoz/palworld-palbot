import nextcord
import aiosqlite
import os
import psycopg2
from utils.translations import t
from utils.database import CONFIG_PG, IsPostgreSQL

DATABASE_PATH = os.path.join('data', 'kits.db')



async def get_kit(kit_name):
    if IsPostgreSQL:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT commands, description, price FROM kits WHERE name = %s', (kit_name,))
                return cursor.fetchone()
        except psycopg2.Error as e:
            print(f"Error fetching kit: {e}")
            return None
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute('SELECT commands, description, price FROM kits WHERE name = ?', (kit_name,))
            return await cursor.fetchone()



async def save_kit(kit_name, commands, description, price):
    if IsPostgreSQL:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute(''' 
                    INSERT INTO kits (name, commands, description, price)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT(name) DO UPDATE SET commands=excluded.commands, description=excluded.description, price=excluded.price
                ''', (kit_name, commands, description, int(price)))
                conn.commit()
        except psycopg2.Error as e:
            print(f"Error saving kit: {e}")
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute(''' 
                INSERT INTO kits (name, commands, description, price)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET commands=excluded.commands, description=excluded.description, price=excluded.price
            ''', (kit_name, commands, description, int(price)))
            await db.commit()



async def delete_kit(kit_name):
    if IsPostgreSQL:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('DELETE FROM kits WHERE name = %s', (kit_name,))
                conn.commit()
        except psycopg2.Error as e:
            print(f"Error deleting kit: {e}")
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute('DELETE FROM kits WHERE name = ?', (kit_name,))
            await db.commit()



async def autocomplete_kits(current: str):
    if IsPostgreSQL:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT name FROM kits WHERE name LIKE %s', (f'%{current}%',))
                kits = cursor.fetchall()
            return [kit[0] for kit in kits]
        except psycopg2.Error as e:
            print(f"Error autocompleting kits: {e}")
            return []
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute('SELECT name FROM kits WHERE name LIKE ?', (f'%{current}%',))
            kits = await cursor.fetchall()
        return [kit[0] for kit in kits]




async def fetch_all_kits():
    if IsPostgreSQL:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT name, commands, description, price FROM kits')
                kits = cursor.fetchall()
            return kits
        except psycopg2.Error as e:
            print(f"Error fetching all kits: {e}")
            return []
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute('SELECT name, commands, description, price FROM kits')
            kits = await cursor.fetchall()
        return kits

async def load_shop_items():
    shop_items = {}
    if IsPostgreSQL:
        conn = psycopg2.connect(**CONFIG_PG)
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT name, description, price FROM kits WHERE price > 0')
                kits = cursor.fetchall()
                for kit in kits:
                    commands, description, price = await get_kit(kit[0])
                    shop_items[kit[0]] = {
                        "commands": commands,
                        "description": description,
                        "price": price
                    }
        except psycopg2.Error as e:
            print(f"Error loading shop items: {e}")
        finally:
            conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute('SELECT name, description, price FROM kits WHERE price > 0')
            kits = await cursor.fetchall()
            for kit in kits:
                commands, description, price = await get_kit(kit[0])
                shop_items[kit[0]] = {
                    "commands": commands,
                    "description": description,
                    "price": price
                }
    return shop_items

class KitModal(nextcord.ui.Modal):
    def __init__(self, title, kit_name="", commands="", description="", price="0"):
        super().__init__(title=title)
        self.add_item(nextcord.ui.TextInput(label=t("Modals", "kitmodal.kit_name_label"), default_value=kit_name))
        self.add_item(nextcord.ui.TextInput(label=t("Modals", "kitmodal.commands_label"), default_value=commands, style=nextcord.TextInputStyle.paragraph))
        self.add_item(nextcord.ui.TextInput(label=t("Modals", "kitmodal.description_label"), default_value=description))
        self.add_item(nextcord.ui.TextInput(label=t("Modals", "kitmodal.price_label"), default_value=price))

    async def callback(self, interaction: nextcord.Interaction):
        kit_name = self.children[0].value
        commands = self.children[1].value
        description = self.children[2].value
        price = self.children[3].value

        await save_kit(kit_name, commands, description, price)
        
        await interaction.client.get_cog('ShopCog').load_shop_items()
        
        await interaction.response.send_message(t("Modals", "kitmodal.success_message").format(kit_name=kit_name), ephemeral=True)