# bot/core/decorators.py
from functools import wraps
from pyrogram.types import Message
from bot.core.database import get_member_role, Role

def require_role(required_role: Role):
    def decorator(func):
        @wraps(func)
        async def wrapper(client: "Bot", message: Message, *args, **kwargs):
            user_id = message.from_user.id
            chat_id = message.chat.id

            # The bot owner (from .env file) bypasses all permission checks
            if user_id == client.owner_id:
                return await func(client, message, *args, **kwargs)

            # Get the user's role from the database for this specific group
            user_role = await get_member_role(client.db, user_id, chat_id)

            # Check if the user has a role and if its value is high enough
            if user_role and user_role.value >= required_role.value:
                return await func(client, message, *args, **kwargs)
            else:
                await message.reply_text(
                    "❌ You don't have enough permissions to use this command."
                )
                return None
        return wrapper
    return decorator