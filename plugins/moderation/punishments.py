# plugins/moderation/punishments.py
from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions

from bot.core.decorators import require_role
from bot.core.database import Role, add_warning_and_get_count, add_group_if_not_exists, add_user_if_not_exists
from bot.core.helpers import parse_time

# --- Mute / Unmute ---

@Client.on_message(filters.group & filters.command("mute"))
@require_role(Role.ADMIN)
async def mute_member(client: "Bot", message: Message):
    if not message.reply_to_message:
        await message.reply_text("Please reply to a user to mute them.")
        return

    user_to_mute = message.reply_to_message.from_user
    duration_str = message.command[1] if len(message.command) > 1 else "0"
    until_date = parse_time(duration_str)

    await message.chat.restrict_member(
        user_id=user_to_mute.id,
        permissions=ChatPermissions(), # No permissions = Muted
        until_date=until_date
    )

    duration_text = f" for {duration_str}" if until_date else " permanently"
    await message.reply_text(f"🔇 Muted {user_to_mute.mention}{duration_text}.")

@Client.on_message(filters.group & filters.command("unmute"))
@require_role(Role.ADMIN)
async def unmute_member(client: "Bot", message: Message):
    if not message.reply_to_message:
        await message.reply_text("Please reply to a user to unmute them.")
        return

    user_to_unmute = message.reply_to_message.from_user
    await message.chat.unban_member(user_id=user_to_unmute.id) # unban_member also unmutes
    await message.reply_text(f"🔊 Unmuted {user_to_unmute.mention}.")

# --- Ban / Unban ---

@Client.on_message(filters.group & filters.command("ban"))
@require_role(Role.MANAGER)
async def ban_member(client: "Bot", message: Message):
    if not message.reply_to_message:
        await message.reply_text("Please reply to a user to ban them.")
        return

    user_to_ban = message.reply_to_message.from_user
    duration_str = message.command[1] if len(message.command) > 1 else "0"
    until_date = parse_time(duration_str)

    await message.chat.ban_member(user_id=user_to_ban.id, until_date=until_date)

    duration_text = f" for {duration_str}" if until_date else " permanently"
    await message.reply_text(f"🔨 Banned {user_to_ban.mention}{duration_text}.")


@Client.on_message(filters.group & filters.command("unban"))
@require_role(Role.MANAGER)
async def unban_member(client: "Bot", message: Message):
    # Unbanning requires a user ID or username, not a reply
    if len(message.command) < 2:
        await message.reply_text("Please specify a user ID or username to unban.")
        return

    user_to_unban = message.command[1]
    try:
        await client.unban_chat_member(message.chat.id, user_to_unban)
        await message.reply_text(f"✅ Unbanned {user_to_unban}.")
    except Exception as e:
        await message.reply_text(f"Error: {e}")

# --- Kick / Warn ---

@Client.on_message(filters.group & filters.command("kick"))
@require_role(Role.ADMIN)
async def kick_member(client: "Bot", message: Message):
    if not message.reply_to_message:
        await message.reply_text("Please reply to a user to kick them.")
        return

    user_to_kick = message.reply_to_message.from_user
    await message.chat.ban_member(user_id=user_to_kick.id)
    await message.chat.unban_member(user_id=user_to_kick.id) # Kicking is just a quick ban/unban
    await message.reply_text(f"👢 Kicked {user_to_kick.mention}.")


@Client.on_message(filters.group & filters.command("warn"))
@require_role(Role.ASSISTANT)
async def warn_member(client: "Bot", message: Message):
    if not message.reply_to_message:
        await message.reply_text("Please reply to a user to warn them.")
        return

    user_to_warn = message.reply_to_message.from_user
    warner = message.from_user

    await add_group_if_not_exists(client.db, message.chat.id, message.chat.title)
    await add_user_if_not_exists(client.db, user_to_warn.id, user_to_warn.first_name, user_to_warn.username, user_to_warn.is_bot)
    await add_user_if_not_exists(client.db, warner.id, warner.first_name, warner.username, warner.is_bot)

    warn_count = await add_warning_and_get_count(client.db, user_to_warn.id, message.chat.id, warner.id)

    # Auto-ban on 3 warnings
    if warn_count >= 3:
        await message.chat.ban_member(user_id=user_to_warn.id)
        await message.reply_text(
            f"⚠️ {user_to_warn.mention} has received their 3rd warning and has been banned."
        )
    else:
        await message.reply_text(
            f"⚠️ Warned {user_to_warn.mention}. They now have {warn_count}/3 warnings."
        )