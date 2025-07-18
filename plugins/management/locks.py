# plugins/management/locks.py
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatType

from bot.core.decorators import require_role
from bot.core.database import Role, set_group_lock, get_group_locks, get_member_role

VALID_LOCKS = ["media", "links", "all"] # "all" locks everything

# --- Lock/Unlock Commands ---

@Client.on_message(filters.group & filters.command(["lock", "unlock"]))
@require_role(Role.ADMIN)
async def lock_unlock_command(client: "Bot", message: Message):
    if len(message.command) < 2 or message.command[1] not in VALID_LOCKS:
        await message.reply_text(f"Invalid usage. Valid locks: {', '.join(VALID_LOCKS)}")
        return

    lock_type = message.command[1]
    is_locking = message.command[0].lower() == "lock"
    status_text = "Locked" if is_locking else "Unlocked"

    if lock_type == "all":
        for lock in VALID_LOCKS:
            if lock != "all":
                await set_group_lock(client.db, message.chat.id, lock, is_locking)
    else:
        await set_group_lock(client.db, message.chat.id, lock_type, is_locking)

    await message.reply_text(f"✅ Successfully **{status_text}** `{lock_type}`.")

# --- Enforcement Handler ---

# The group=-1 makes this handler run before others.
# This is crucial for catching and deleting messages before they are processed by other plugins.
@Client.on_message(filters.group, group=-1)
async def enforcement_handler(client: "Bot", message: Message):
    # We don't want to check messages from private chats or channels
    if message.chat.type != ChatType.SUPERGROUP:
        return

    # Admins are immune to locks
    user_role = await get_member_role(client.db, message.from_user.id, message.chat.id)
    if message.from_user and (message.from_user.id == client.owner_id or (user_role and user_role.value >= Role.ADMIN.value)):
         return

    locks = await get_group_locks(client.db, message.chat.id)
    if not locks:
        return

    # Lock "all" is a catch-all
    if locks.get("all", False):
        await message.delete()
        return

    # Lock specific message types
    if locks.get("links", False) and (message.text or message.caption):
        text = message.text or message.caption
        if "http://" in text or "https://" in text or "t.me" in text:
            await message.delete()
            return

    if locks.get("media", False) and (message.photo or message.video or message.document or message.sticker):
        await message.delete()
        return