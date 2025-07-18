import asyncpg
from typing import Optional
import json

from enum import Enum

class Role(Enum):
    ASSISTANT = 1
    ADMIN = 2
    MANAGER = 3
    OWNER = 4

async def add_user_if_not_exists(pool: asyncpg.Pool, user_id: int, first_name: str, username: Optional[str], is_bot: bool):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (user_id, first_name, username, is_bot)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id) DO NOTHING;
            """,
            user_id, first_name, username, is_bot
        )

async def add_group_if_not_exists(pool: asyncpg.Pool, chat_id: int, title: str):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO groups (chat_id, title)
            VALUES ($1, $2)
            ON CONFLICT (chat_id) DO NOTHING;
            """,
            chat_id, title
        )

async def set_member_role(pool: asyncpg.Pool, user_id: int, chat_id: int, role: Role):
    role_name_str = role.name.lower()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO group_members (user_id, chat_id, role)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id, chat_id)
            DO UPDATE SET role = EXCLUDED.role;
            """,
            user_id, chat_id, role_name_str
        )

async def get_member_role(pool: asyncpg.Pool, user_id: int, chat_id: int) -> Optional[Role]:
    async with pool.acquire() as conn:
        role_str = await conn.fetchval(
            "SELECT role FROM group_members WHERE user_id = $1 AND chat_id = $2",
            user_id, chat_id
        )
        if role_str:
            return Role[role_str.upper()]
    return None

async def remove_member_role(pool: asyncpg.Pool, user_id: int, chat_id: int):
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM group_members WHERE user_id = $1 AND chat_id = $2",
            user_id, chat_id
        )


# Add this to the end of bot/core/database.py
async def add_warning_and_get_count(pool: asyncpg.Pool, user_id: int, chat_id: int, warner_id: int) -> int:
    """Adds a warning and returns the new total warning count for the user in that chat."""
    async with pool.acquire() as conn:
        # Add the new warning
        await conn.execute(
            "INSERT INTO warnings (user_id, chat_id, warner_id) VALUES ($1, $2, $3)",
            user_id, chat_id, warner_id
        )
        # Get the new total count
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM warnings WHERE user_id = $1 AND chat_id = $2",
            user_id, chat_id
        )
        return count
    
# Add these to the end of bot/core/database.py

async def set_group_lock(pool: asyncpg.Pool, chat_id: int, lock_type: str, status: bool):
    """Sets a specific lock type to true or false for a group."""
    async with pool.acquire() as conn:
        # This query updates the 'locks' object within the 'config' JSONB column.
        # The '||' operator merges JSON objects.
        await conn.execute(
            """
            UPDATE groups
            SET config = config || jsonb_build_object('locks', jsonb_build_object($1::text, $2::boolean))
            WHERE chat_id = $3;
            """,
            lock_type, status, chat_id
        )

async def get_group_locks(pool: asyncpg.Pool, chat_id: int) -> dict:
    """Gets the lock configuration for a group."""
    async with pool.acquire() as conn:
        # This query now fetches only the 'locks' object from the JSON
        locks_str = await conn.fetchval(
            "SELECT config -> 'locks' FROM groups WHERE chat_id = $1",
            chat_id
        )
        # asyncpg returns json as a string, so we must parse it
        if locks_str:
            return json.loads(locks_str)
        return {}

# Add these to the end of bot/core/database.py

async def add_filter(pool: asyncpg.Pool, chat_id: int, filter_name: str, reply_text: str, reply_type: str, file_id: str):
    """Adds a new filter to the database."""
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO filters (chat_id, filter_name, reply_text, reply_type, file_id)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (chat_id, filter_name) DO UPDATE SET
            reply_text = EXCLUDED.reply_text,
            reply_type = EXCLUDED.reply_type,
            file_id = EXCLUDED.file_id;
            """,
            chat_id, filter_name, reply_text, reply_type, file_id
        )

async def remove_filter(pool: asyncpg.Pool, chat_id: int, filter_name: str):
    """Removes a filter from the database."""
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM filters WHERE chat_id = $1 AND filter_name = $2",
            chat_id, filter_name
        )

async def get_all_filters(pool: asyncpg.Pool, chat_id: int):
    """Gets all filters for a specific chat."""
    async with pool.acquire() as conn:
        return await conn.fetch("SELECT * FROM filters WHERE chat_id = $1", chat_id)
    

# Add these to the end of bot/core/database.py

async def add_banned_name_pattern(pool: asyncpg.Pool, chat_id: int, pattern: str):
    """Adds a new banned name pattern for a group."""
    async with pool.acquire() as conn:
        # This query appends a new pattern to the 'banned_names' array in the config
        await conn.execute(
            """
            UPDATE groups
            SET config = jsonb_set(
                config,
                '{banned_names}',
                (COALESCE(config->'banned_names', '[]'::jsonb) || $1::jsonb),
                true
            )
            WHERE chat_id = $2;
            """,
            f'"{pattern}"', chat_id
        )

async def remove_banned_name_pattern(pool: asyncpg.Pool, chat_id: int, pattern: str):
    """Removes a banned name pattern from a group."""
    async with pool.acquire() as conn:
        # This query removes a specific element from the 'banned_names' array
        await conn.execute(
            """
            UPDATE groups
            SET config = jsonb_set(
                config,
                '{banned_names}',
                (config->'banned_names') - $1
            )
            WHERE chat_id = $2;
            """,
            pattern, chat_id
        )

async def get_banned_name_patterns(pool: asyncpg.Pool, chat_id: int) -> list:
    """Gets the list of banned name patterns for a group."""
    async with pool.acquire() as conn:
        patterns_json = await conn.fetchval(
            "SELECT config -> 'banned_names' FROM groups WHERE chat_id = $1",
            chat_id
        )
        if patterns_json:
            return json.loads(patterns_json)
        return []
    

# Add these to the end of bot/core/database.py

async def log_user_activity(pool: asyncpg.Pool, chat_id: int, user_id: int):
    """Logs a message from a user, incrementing their count."""
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO group_activity (chat_id, user_id)
            VALUES ($1, $2)
            ON CONFLICT (chat_id, user_id) DO UPDATE SET
            message_count = group_activity.message_count + 1,
            last_message_timestamp = NOW();
            """,
            chat_id, user_id
        )

async def get_top_active_users(pool: asyncpg.Pool, chat_id: int, limit: int = 5):
    """Gets the most active users in a group."""
    async with pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT u.first_name, ga.message_count
            FROM group_activity ga
            JOIN users u ON ga.user_id = u.user_id
            WHERE ga.chat_id = $1
            ORDER BY ga.message_count DESC
            LIMIT $2;
            """,
            chat_id, limit
        )

async def get_total_group_messages(pool: asyncpg.Pool, chat_id: int) -> int:
    """Gets the total message count for a group."""
    async with pool.acquire() as conn:
        count = await conn.fetchval(
            "SELECT SUM(message_count) FROM group_activity WHERE chat_id = $1",
            chat_id
        )
        return count or 0