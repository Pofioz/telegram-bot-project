# plugins/moderation/roles.py
from pyrogram import Client, filters
from pyrogram.types import Message
from bot.core.database import (
    add_user_if_not_exists,
    add_group_if_not_exists,
    set_member_role,
    remove_member_role,
    Role
)
from bot.core.decorators import require_role

# A helper to map command text to Role objects
ROLE_MAP = {
    "setassistant": Role.ASSISTANT,
    "setadmin": Role.ADMIN,
    "setmanager": Role.MANAGER,
    "setowner": Role.OWNER,
}

@Client.on_message(filters.group & filters.command(list(ROLE_MAP.keys())))
@require_role(Role.OWNER)  # Only the group owner can promote others
async def promote_member(client: "Bot", message: Message):
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.reply_text("Please reply to a user's message to promote them.")
        return

    chat_id = message.chat.id
    chat_title = message.chat.title
    promoted_user = message.reply_to_message.from_user
    command = message.command[0].lower()
    role_to_set = ROLE_MAP.get(command)

    # Add the group and user to our database if they aren't there yet
    await add_group_if_not_exists(client.db, chat_id, chat_title)
    await add_user_if_not_exists(client.db, promoted_user.id, promoted_user.first_name, promoted_user.username, promoted_user.is_bot)

    # Set the role in the database
    await set_member_role(client.db, promoted_user.id, chat_id, role_to_set)

    await message.reply_text(
        f"✅ Successfully promoted {promoted_user.mention} to **{role_to_set.name.capitalize()}**."
    )

@Client.on_message(filters.group & filters.command("demote"))
@require_role(Role.OWNER)  # Only the group owner can demote others
async def demote_member(client: "Bot", message: Message):
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.reply_text("Please reply to a user's message to demote them.")
        return

    chat_id = message.chat.id
    demoted_user = message.reply_to_message.from_user

    await remove_member_role(client.db, demoted_user.id, chat_id)

    await message.reply_text(
        f"✅ Successfully demoted {demoted_user.mention}. They now have no special role."
    )