# bot/main.py
import asyncio
import logging

import asyncpg
from environs import Env
from loguru import logger
from pyrogram import Client
from pytgcalls import PyTgCalls # <-- NEW IMPORT

# ... (keep the rest of your imports and config setup) ...
# --- Environment Setup ---
env = Env()
env.read_env()

API_ID = env.int("API_ID")
API_HASH = env.str("API_HASH")
BOT_TOKEN = env.str("BOT_TOKEN")
OWNER_ID = env.int("OWNER_ID")
DB_USER = env.str("DB_USER")
DB_PASS = env.str("DB_PASS")
DB_NAME = env.str("DB_NAME")
DB_HOST = env.str("DB_HOST")

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)
loguru_logger = logger
loguru_logger.add(
    "logs/bot.log", rotation="10 MB", retention="10 days", level="INFO"
)

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="my_bot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="plugins"),
        )
        self.log = loguru_logger
        self.owner_id = OWNER_ID
        self.db: asyncpg.Pool = None
        self.voice_client: PyTgCalls = None # <-- NEW ATTRIBUTE

    async def start(self):
        self.log.info("Starting bot...")
        await super().start()

        # --- Database Connection ---
        self.log.info("Connecting to the database...")
        try:
            self.db = await asyncpg.create_pool(
                user=DB_USER, password=DB_PASS, database=DB_NAME, host=DB_HOST
            )
            await self.db.execute("SELECT 1")
            self.log.success("Database connection successful.")
        except Exception as e:
            self.log.error(f"Could not connect to database: {e}")
            exit()

        # --- Voice Client Setup ---
        self.log.info("Starting voice client...")
        self.voice_client = PyTgCalls(self) # <-- NEW
        await self.voice_client.start()    # <-- NEW

        me = await self.get_me()
        self.log.success(f"Bot started as {me.first_name} (@{me.username})!")

    async def stop(self):
        self.log.warning("Stopping bot...")
        if self.db:
            await self.db.close()
            self.log.info("Database connection closed.")

        if self.voice_client.is_running: # <-- NEW
            await self.voice_client.stop()   # <-- NEW

        await super().stop()
        self.log.info("Bot stopped.")

async def main():
    bot = Bot()
    try:
        await bot.start()
        await asyncio.Event().wait()
    except Exception as e:
        bot.log.exception(f"An unexpected error occurred: {e}")
    finally:
        await bot.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        loguru_logger.info("Bot execution stopped manually.")