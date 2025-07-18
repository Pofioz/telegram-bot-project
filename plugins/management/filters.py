# plugins/management/filters.py
from pyrogram import Client, filters
from pyrogram.types import Message

from bot.core.decorators import require_role
from bot.core.database import Role, add_filter, remove_filter, get_all_filters

@Client.on_message(filters.group & filters.command("addfilter"))
@require_role(Role.ADMIN)
async def add_filter_command(client: "Bot", message: Message):
    if not message.reply_to_message:
        await message.reply_text("Please reply to a message to set it as a filter reply.")
        return

    # The trigger is the word after /addfilter
    try:
        filter_name = message.command[1].lower()
    except IndexError:
        await message.reply_text("Usage: `/addfilter <trigger>` while replying to a message.")
        return

    reply_message = message.reply_to_message
    reply_text = reply_message.text or reply_message.caption
    file_id = None
    reply_type = "text"

    if reply_message.sticker:
        reply_type = "sticker"
        file_id = reply_message.sticker.file_id
    elif reply_message.photo:
        reply_type = "photo"
        file_id = reply_message.photo.file_id
    # Add more types like video, document, etc. as needed

    await add_filter(client.db, message.chat.id, filter_name, reply_text, reply_type, file_id)
    await message.reply_text(f"✅ Filter `{filter_name}` saved.")


@Client.on_message(filters.group & filters.command(["delfilter", "stop"]))
@require_role(Role.ADMIN)
async def remove_filter_command(client: "Bot", message: Message):
    try:
        filter_name = message.command[1].lower()
    except IndexError:
        await message.reply_text("Usage: `/delfilter <trigger>`")
        return

    await remove_filter(client.db, message.chat.id, filter_name)
    await message.reply_text(f"✅ Filter `{filter_name}` removed.")


@Client.on_message(filters.group & filters.command("filters"))
async def list_filters_command(client: "Bot", message: Message):
    all_filters = await get_all_filters(client.db, message.chat.id)
    if not all_filters:
        await message.reply_text("There are no filters in this chat.")
        return

    filter_names = [f"`{f['filter_name']}`" for f in all_filters]
    await message.reply_text("Available filters in this chat:\n" + "\n".join(filter_names))


# This handler will check every message for a filter trigger
# The group=2 makes it run after the lock handler but before normal command handlers
@Client.on_message(filters.group & filters.text, group=2)
async def filter_enforcement_handler(client: "Bot", message: Message):
    # This new line makes the function exit immediately if the message is a command
    if message.text and message.text.startswith("/"):
        return

    all_filters = await get_all_filters(client.db, message.chat.id)
    if not all_filters:
        return

    for f in all_filters:
        # Using f" {f['filter_name']} " ensures we match whole words
        if f" {f['filter_name']} " in f" {message.text.lower()} ":
            reply_type = f['reply_type']

            if reply_type == "text":
                await message.reply_text(f['reply_text'], quote=False)
            elif reply_type == "sticker":
                await message.reply_sticker(f['file_id'], quote=False)
            elif reply_type == "photo":
                await message.reply_photo(f['file_id'], caption=f['reply_text'], quote=False)

            break