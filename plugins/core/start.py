from pyrogram import Client, filters
from pyrogram.types import Message

@Client.on_message(filters.command("start") & filters.private)
async def start_private(client: "Bot", message: Message):
    """Handler for the /start command in private chats."""
    await message.reply_text(
        f"Hello {message.from_user.mention}! I am your friendly group manager bot.\n"
        "Add me to a group and make me an admin to get started."
    )

@Client.on_message(filters.command("help"))
async def help_command(client: "Bot", message: Message):
    """Shows a generic help message."""
    help_text = (
        "**🤖 Bot Help**\n\n"
        "I am a group management and music bot. My commands are organized into modules."
    )
    await message.reply_text(help_text)