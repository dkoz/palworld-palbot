import nextcord
import aiosqlite
import os

DATABASE_PATH = os.path.join('data', 'kits.db')

async def init_kitdb():
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
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT commands, description, price FROM kits WHERE name = ?', (kit_name,))
        return await cursor.fetchone()

async def save_kit(kit_name, commands, description, price):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            INSERT INTO kits (name, commands, description, price)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET commands=excluded.commands, description=excluded.description, price=excluded.price
        ''', (kit_name, commands, description, int(price)))
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

async def load_shop_items():
    shop_items = {}
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
        self.add_item(nextcord.ui.TextInput(label="Kit Name", default_value=kit_name))
        self.add_item(nextcord.ui.TextInput(label="Commands (JSON list)", default_value=commands, style=nextcord.TextInputStyle.paragraph))
        self.add_item(nextcord.ui.TextInput(label="Description", default_value=description))
        self.add_item(nextcord.ui.TextInput(label="Price", default_value=price))

    async def callback(self, interaction: nextcord.Interaction):
        kit_name = self.children[0].value
        commands = self.children[1].value
        description = self.children[2].value
        price = self.children[3].value

        await save_kit(kit_name, commands, description, price)
        await interaction.response.send_message(f"Kit '{kit_name}' has been saved.", ephemeral=True)
