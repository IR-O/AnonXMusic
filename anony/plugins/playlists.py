# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.

from pyrogram import filters, types

from anony import app, db, lang, yt
from anony.helpers import utils


# 🔥 GET USER PLAYLIST
async def get_playlist(user_id):
    return await db.get_playlist(user_id) or []


# 🔥 SAVE PLAYLIST
async def save_playlist(user_id, playlist):
    await db.set_playlist(user_id, playlist)


# 🔥 ADD TO PLAYLIST
@app.on_message(filters.command("addplaylist"))
@lang.language()
async def add_playlist(_, m: types.Message):
    if len(m.command) < 2:
        return await m.reply_text("Usage: /addplaylist song name")

    query = " ".join(m.command[1:])
    result = await yt.search(query, m.id)

    if not result:
        return await m.reply_text("❌ Song not found")

    playlist = await get_playlist(m.from_user.id)
    playlist.append({
        "title": result.title,
        "id": result.id,
        "duration": result.duration,
        "url": result.url,
    })

    await save_playlist(m.from_user.id, playlist)

    await m.reply_text(f"✅ Added to playlist:\n{result.title}")


# 🔥 SHOW PLAYLIST
@app.on_message(filters.command("playlist"))
@lang.language()
async def show_playlist(_, m: types.Message):
    playlist = await get_playlist(m.from_user.id)

    if not playlist:
        return await m.reply_text("❌ Your playlist is empty")

    text = "🎶 Your Playlist:\n\n"

    for i, song in enumerate(playlist, start=1):
        text += f"{i}. {song['title']} ({song['duration']})\n"

    await m.reply_text(text)


# 🔥 DELETE SONG
@app.on_message(filters.command("delplaylist"))
@lang.language()
async def del_playlist(_, m: types.Message):
    if len(m.command) < 2:
        return await m.reply_text("Usage: /delplaylist number")

    playlist = await get_playlist(m.from_user.id)

    if not playlist:
        return await m.reply_text("❌ Playlist empty")

    try:
        index = int(m.command[1]) - 1
        removed = playlist.pop(index)
    except:
        return await m.reply_text("❌ Invalid number")

    await save_playlist(m.from_user.id, playlist)

    await m.reply_text(f"🗑 Removed: {removed['title']}")


# 🔥 CLEAR PLAYLIST
@app.on_message(filters.command("clearplaylist"))
@lang.language()
async def clear_playlist(_, m: types.Message):
    await save_playlist(m.from_user.id, [])
    await m.reply_text("🧹 Playlist cleared")


# 🔥 PLAY PLAYLIST
@app.on_message(filters.command("playplaylist"))
@lang.language()
async def play_playlist(_, m: types.Message):
    playlist = await get_playlist(m.from_user.id)

    if not playlist:
        return await m.reply_text("❌ Playlist empty")

    chat_id = m.chat.id

    for song in playlist:
        track = await yt.search(song["id"], m.id)
        if track:
            from anony import queue
            queue.add(chat_id, track)

    await m.reply_text("▶️ Playlist added to queue")
