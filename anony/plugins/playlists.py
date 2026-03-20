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


# 🔥 ADD TO PLAYLIST (MANUAL)
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

    # ❌ Duplicate check
    if any(s["id"] == result.id for s in playlist):
        return await m.reply_text("⚠️ Already in playlist")

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


# 🔥 PLAY PLAYLIST (FIXED)
@app.on_message(filters.command("playplaylist"))
@lang.language()
async def play_playlist(_, m: types.Message):
    from anony import queue, anon

    playlist = await get_playlist(m.from_user.id)

    if not playlist:
        return await m.reply_text("❌ Playlist empty")

    chat_id = m.chat.id
    msg = await m.reply_text("⏳ Starting playlist...")

    first = True

    for song in playlist:
        track = await yt.search(song["id"], m.id)

        if not track:
            continue

        if first:
            first = False

            # 🔥 FIRST SONG → VC JOIN + PLAY
            await anon.play_media(
                chat_id=chat_id,
                message=msg,
                media=track
            )
        else:
            queue.add(chat_id, track)

    await msg.edit_text("▶️ Playlist started")


# 🔥 SAVE BUTTON CALLBACK (MAIN FEATURE)
@app.on_callback_query(filters.regex(r"^controls save"))
async def save_cb(_, cb):
    data = cb.data.split()

    if len(data) < 4:
        return await cb.answer("❌ Error", show_alert=True)

    user_id = cb.from_user.id
    track_id = data[3]

    track = await yt.search(track_id, cb.message.id)

    if not track:
        return await cb.answer("❌ Song not found", show_alert=True)

    playlist = await get_playlist(user_id)

    # ❌ Duplicate check
    if any(s["id"] == track.id for s in playlist):
        return await cb.answer("⚠️ Already in playlist", show_alert=True)

    song = {
        "title": track.title,
        "id": track.id,
        "duration": track.duration,
        "url": track.url,
    }

    await db.add_to_playlist(user_id, song)

    await cb.answer("✅ Saved to playlist", show_alert=True)
