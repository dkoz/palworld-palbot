import nextcord
import aiosqlite
import os
import psycopg2
from urllib.parse import urlparse
from psycopg2 import sql
import utils.settings as settings
from utils.translations import t

DATABASE_PATH = os.path.join('data', 'kits.db')
CONFIG_KITS_PG = ''



async def init_kitdb():
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
        config_kits = {
            'user': conn_params.get('user'),
            'password': conn_params.get('password'),
            'host': conn_params.get('host'),
            'port': conn_params.get('port'),
        }

        #defines the name of the database
        database_name = 'kits_db' 

        #Connect to PostgreSQL database
        try:
            #First connect to the default database (template1)
            connection = psycopg2.connect(**config_kits, dbname="template1")
            connection.autocommit = True
            cursor = connection.cursor()

            #Check if the database already exists
            cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{database_name}'")
            result = cursor.fetchone()

            if not result:
                cursor.execute(f"CREATE DATABASE {database_name}")
            #    print(f"Database '{database_name}' created successfully.")
            #else:
            #    print(f"Database '{database_name}' already exists.")

        except psycopg2.Error as e:
            print(f"Error: {e}")
        finally:
            cursor.close()
            connection.close()

        #Connect to newly created database
        config_kits['dbname'] = database_name

        global CONFIG_KITS_PG
        CONFIG_KITS_PG = config_kits

        try:
            connection = psycopg2.connect(**CONFIG_KITS_PG)
            connection.autocommit = True
            cursor = connection.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS kits (
                    name VARCHAR(255) PRIMARY KEY,
                    commands VARCHAR(255),
                    description VARCHAR(255),
                    price INTEGER
                )
            ''')
        except psycopg2.Error as e:
            print(f"Error connecting to PostgreSQL: {e}")
        finally:
            if connection:
                cursor.close()
                connection.close()
    else:

        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS kits (
                    name TEXT PRIMARY KEY,
                    commands TEXT,
                    description TEXT,
                    price INTEGER
                )
            ''')
            await db.commit()


async def get_kit(kit_name):
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_KITS_PG)
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
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_KITS_PG)
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
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_KITS_PG)
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
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_KITS_PG)
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
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_KITS_PG)
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
    if settings.connection_string:
        conn = psycopg2.connect(**CONFIG_KITS_PG)
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