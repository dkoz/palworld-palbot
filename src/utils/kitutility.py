import nextcord
import aiosqlite
import os
from src.utils.translations import t

DATABASE_PATH = os.path.join('data', 'kits.db')

async def init_kitdb():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS kits (
                name TEXT PRIMARY KEY,
                commands TEXT,
                description TEXT,
                price INTEGER,
                category TEXT DEFAULT 'main'
            )
        ''')
        try:
            await db.execute("ALTER TABLE kits ADD COLUMN category TEXT DEFAULT 'main'")
        except aiosqlite.OperationalError:
            pass
        await db.execute("UPDATE kits SET category = 'main' WHERE category IS NULL")
        await db.commit()

async def get_kit(kit_name):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT commands, description, price, category FROM kits WHERE name = ?', (kit_name,))
        return await cursor.fetchone()

async def save_kit(kit_name, commands, description, price, category='main'):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            INSERT INTO kits (name, commands, description, price, category)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE 
              SET commands=excluded.commands,
                  description=excluded.description,
                  price=excluded.price,
                  category=excluded.category
        ''', (kit_name, commands, description, int(price), category))
        await db.commit()

async def delete_kit(kit_name):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('DELETE FROM kits WHERE name = ?', (kit_name,))
        await db.commit()

async def autocomplete_kits(current: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT name FROM kits WHERE name LIKE ?', (f'%{current}%',))
        kits = await cursor.fetchall()
    return [kit[0] for kit in kits]

async def fetch_all_kits():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT name, commands, description, price, category FROM kits')
        kits = await cursor.fetchall()
    return kits

async def load_shop_items():
    shop_items = {}
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT name, description, price, category FROM kits WHERE price > 0')
        kits = await cursor.fetchall()
        for kit in kits:
            name = kit[0]
            description = kit[1]
            price = kit[2]
            category = kit[3]
            cmd_cursor = await db.execute('SELECT commands FROM kits WHERE name = ?', (name,))
            commands_data = await cmd_cursor.fetchone()
            commands = commands_data[0] if commands_data else "[]"
            shop_items[name] = {
                "commands": commands,
                "description": description,
                "price": price,
                "category": category
            }
    return shop_items

class KitModal(nextcord.ui.Modal):
    def __init__(self, title, kit_name="", commands="", description="", price="0", category="main"):
        super().__init__(title=title)
        self.add_item(nextcord.ui.TextInput(label=t("Modals", "kitmodal.kit_name_label"), default_value=kit_name))
        self.add_item(nextcord.ui.TextInput(label=t("Modals", "kitmodal.commands_label"), default_value=commands, style=nextcord.TextInputStyle.paragraph))
        self.add_item(nextcord.ui.TextInput(label=t("Modals", "kitmodal.description_label"), default_value=description))
        self.add_item(nextcord.ui.TextInput(label=t("Modals", "kitmodal.price_label"), default_value=price))
        self.add_item(nextcord.ui.TextInput(label=t("Modals", "kitmodal.category_label"), default_value=category, placeholder="main"))

    async def callback(self, interaction: nextcord.Interaction):
        kit_name = self.children[0].value
        commands = self.children[1].value
        description = self.children[2].value
        price = self.children[3].value
        category = self.children[4].value.strip() or "main"
        await save_kit(kit_name, commands, description, price, category)
        await interaction.client.get_cog('ShopCog').load_shop_items()
        await interaction.response.send_message(t("Modals", "kitmodal.success_message").format(kit_name=kit_name), ephemeral=True)