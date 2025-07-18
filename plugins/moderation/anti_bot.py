# plugins/moderation/anti_bot.py
import re
from pyrogram import Client, filters
from pyrogram.types import Message

from bot.core.decorators import require_role
from bot.core.database import Role, add_banned_name_pattern, remove_banned_name_pattern, get_banned_name_patterns

# --- Management Commands ---

@Client.on_message(filters.group & filters.command("addbanname"))
@require_role(Role.MANAGER)
async def add_banned_name_command(client: "Bot", message: Message):
    if len(message.command) < 2:
        await message.reply_text("Usage: `/addbanname <pattern>`")
        return

    pattern = " ".join(message.command[1:])
    await add_banned_name_pattern(client.db, message.chat.id, pattern)
    await message.reply_text(f"✅ Added `{pattern}` to the banned name list.")

@Client.on_message(filters.group & filters.command("delbanname"))
@require_role(Role.MANAGER)
async def remove_banned_name_command(client: "Bot", message: Message):
    if len(message.command) < 2:
        await message.reply_text("Usage: `/delbanname <pattern>`")
        return

    pattern = " ".join(message.command[1:])
    await remove_banned_name_pattern(client.db, message.chat.id, pattern)
    await message.reply_text(f"✅ Removed `{pattern}` from the banned name list.")

@Client.on_message(filters.group & filters.command("bannednames"))
async def list_banned_names_command(client: "Bot", message: Message):
    patterns = await get_banned_name_patterns(client.db, message.chat.id)
    if not patterns:
        await message.reply_text("There are no banned name patterns set for this group.")
        return

    text = "Banned Name Patterns:\n" + "\n".join([f"- `{p}`" for p in patterns])
    await message.reply_text(text)


# --- Enforcement Handler for New Members ---

@Client.on_message(filters.new_chat_members, group=-2)
async def anti_bot_handler(client: "Bot", message: Message):
    patterns = await get_banned_name_patterns(client.db, message.chat.id)
    if not patterns:
        return

    for member in message.new_chat_members:
        full_name = f"{member.first_name} {member.last_name or ''}".lower()

        for pattern in patterns:
            if re.search(pattern.lower(), full_name):
                try:
                    # Kick the user and notify the chat
                    await message.chat.ban_member(member.id)
                    await message.chat.unban_member(member.id)
                    await message.reply_text(
                        f"👢 Kicked {member.mention} for having a suspicious name."
                    )
                except Exception as e:
                    await message.reply_text(f"Error kicking bot: {e}")
                break # Stop checking patterns for this user