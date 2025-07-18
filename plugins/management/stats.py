# plugins/management/stats.py
from pyrogram import Client, filters
from pyrogram.types import Message

from bot.core.decorators import require_role
from bot.core.database import Role, log_user_activity, get_top_active_users, get_total_group_messages, add_user_if_not_exists

# --- Activity Logger ---
# This handler runs for every message to log user activity.
# group=-3 makes it run after moderation but before other things.
@Client.on_message(filters.group, group=-3)
async def activity_logger(client: "Bot", message: Message):
    if message.from_user and not message.from_user.is_bot:
        # Ensure user exists in the 'users' table first
        await add_user_if_not_exists(
            client.db,
            message.from_user.id,
            message.from_user.first_name,
            message.from_user.username,
            message.from_user.is_bot
        )
        # Log the activity
        await log_user_activity(client.db, message.chat.id, message.from_user.id)

# --- Stats Commands ---

@Client.on_message(filters.group & filters.command("stats"))
@require_role(Role.ADMIN)
async def group_stats_command(client: "Bot", message: Message):
    chat_id = message.chat.id
    total_messages = await get_total_group_messages(client.db, chat_id)
    total_members = await client.get_chat_members_count(chat_id)

    await message.reply_text(
        f"📊 **Group Statistics**\n\n"
        f"👥 Total Members: `{total_members}`\n"
        f"💬 Total Messages: `{total_messages}`"
    )

@Client.on_message(filters.group & filters.command("topusers"))
@require_role(Role.ADMIN)
async def top_users_command(client: "Bot", message: Message):
    top_users = await get_top_active_users(client.db, message.chat.id)
    if not top_users:
        await message.reply_text("No activity has been recorded yet.")
        return

    text = "🏆 **Top 5 Active Users**\n\n"
    for i, user in enumerate(top_users, 1):
        text += f"{i}. {user['first_name']} - `{user['message_count']}` messages\n"

    await message.reply_text(text)