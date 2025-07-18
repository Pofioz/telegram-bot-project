# plugins/music/play.py
import os
from pyrogram import Client, filters
from pyrogram.types import Message
from py_tgcalls.types import AudioPiped

from bot.core.decorators import require_role
from bot.core.database import Role
from bot.core.music_helpers import get_queue, add_to_queue, get_next_song, download_song

# --- In-memory state to track if a chat is playing ---
PLAYING_STATE = {}

async def start_playback(client: "Bot", chat_id: int):
    """The main function to start playing the next song in the queue."""
    song = get_next_song(chat_id)
    if not song:
        # If queue is empty, leave the voice chat
        await client.voice_client.leave_group_call(chat_id)
        PLAYING_STATE[chat_id] = False
        return

    PLAYING_STATE[chat_id] = True

    try:
        # Join the voice chat
        await client.voice_client.join_group_call(
            chat_id,
            AudioPiped(song['path']),
        )
        await client.send_message(chat_id, f"▶️ Now Playing: **{song['title']}**")
    except Exception as e:
        await client.send_message(chat_id, f"Error playing song: {e}")

# --- PyTgCalls Event Listener ---
# This function runs automatically when a song finishes playing
@Client.on_raw_update()
async def on_stream_end(client: "Bot", update, users, chats):
    if not isinstance(getattr(update, 'message', None), Message) and \
       hasattr(update, 'chat_id') and hasattr(update, 'stream_id'):
        chat_id = update.chat_id
        if PLAYING_STATE.get(chat_id):
            # Start playing the next song
            await start_playback(client, chat_id)


# --- Play Command ---
@Client.on_message(filters.group & filters.command("play"))
@require_role(Role.ADMIN)
async def play_command(client: "Bot", message: Message):
    if len(message.command) < 2:
        await message.reply_text("Usage: `/play <song name or youtube link>`")
        return

    query = " ".join(message.command[1:])
    await message.reply_text(f"Searching for `{query}`...")

    try:
        song_info = await download_song(query)
        add_to_queue(
            chat_id=message.chat.id,
            title=song_info['title'],
            path=song_info['path'],
            requester=message.from_user.mention
        )
        await message.reply_text(f"✅ Added to queue: **{song_info['title']}**")

        # If nothing is currently playing, start playback
        if not PLAYING_STATE.get(message.chat.id):
            await start_playback(client, message.chat.id)

    except Exception as e:
        await message.reply_text(f"Error: {e}")