# bot/core/music_helpers.py
import asyncio
import os
from yt_dlp import YoutubeDL

# This dictionary will hold the queue for each chat
# In a real production bot, you'd use a database (like Redis) for this
queues = {}

def get_queue(chat_id: int):
    """Gets the queue for a specific chat."""
    return queues.get(chat_id, [])

def add_to_queue(chat_id: int, title: str, path: str, requester: str):
    """Adds a song to the queue."""
    if chat_id not in queues:
        queues[chat_id] = []
    queues[chat_id].append({"title": title, "path": path, "requester": requester})

def get_next_song(chat_id: int):
    """Gets the next song from the queue and removes it."""
    queue = get_queue(chat_id)
    return queue.pop(0) if queue else None

def clear_queue(chat_id: int):
    """Clears the queue for a chat."""
    if chat_id in queues:
        queues[chat_id] = []

# --- Music Downloader ---

async def download_song(query: str) -> dict:
    """Downloads a song from YouTube and returns its info."""
    # Options for yt-dlp
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s', # Save to a 'downloads' folder
        'quiet': True,
        'noplaylist': True,
    }

    loop = asyncio.get_event_loop()

    # yt-dlp is not async, so we run it in a separate thread
    with YoutubeDL(ydl_opts) as ydl:
        info = await loop.run_in_executor(
            None, lambda: ydl.extract_info(f"ytsearch:{query}", download=True)
        )

    if 'entries' in info:
        entry = info['entries'][0]
    else:
        entry = info

    # The actual path to the downloaded file
    path = ydl.prepare_filename(entry)

    return {
        "title": entry['title'],
        "path": path
    }