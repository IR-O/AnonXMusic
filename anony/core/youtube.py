# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.

import os
import re
import yt_dlp
import random
import asyncio
import aiohttp
from pathlib import Path

from py_yt import Playlist, VideosSearch

from anony import logger
from anony.helpers import Track, utils


class YouTube:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.cookie_dir = "anony/cookies"
        self.cookies = []
        self.checked = False
        self.warned = False

        # 🔥 API SYSTEM
        self.API_URL = None
        self.FALLBACK_API = "https://shrutibots.site"

        self.regex = re.compile(
            r"(https?://)?(www\.|m\.|music\.)?"
            r"(youtube\.com/(watch\?v=|shorts/|playlist\?list=)|youtu\.be/)"
            r"([A-Za-z0-9_-]{11}|PL[A-Za-z0-9_-]+)"
        )

    # ✅ FIX: Dummy cookies function (ERROR SOLVED)
    async def save_cookies(self, urls: list[str]) -> None:
        logger.info("Cookies disabled (Streaming/API mode)")
        return

    # 🔥 LOAD API
    async def load_api(self):
        if self.API_URL:
            return
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://pastebin.com/raw/rLsBhAQa",
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 200:
                        self.API_URL = (await resp.text()).strip()
                        logger.info("API Loaded")
                    else:
                        self.API_URL = self.FALLBACK_API
        except:
            self.API_URL = self.FALLBACK_API

    # 🔍 SEARCH
    async def search(self, query: str, m_id: int, video: bool = False):
        try:
            results = await VideosSearch(query, limit=1).next()
        except:
            return None

        if results and results["result"]:
            data = results["result"][0]
            return Track(
                id=data["id"],
                title=data["title"][:25],
                duration=data["duration"],
                duration_sec=utils.to_seconds(data["duration"]),
                thumbnail=data["thumbnails"][-1]["url"].split("?")[0],
                url=data["link"],
                channel_name=data["channel"]["name"],
                view_count=data["viewCount"]["short"],
                message_id=m_id,
                video=video,
            )
        return None

    # 📂 PLAYLIST
    async def playlist(self, limit: int, user: str, url: str, video: bool):
        tracks = []
        try:
            plist = await Playlist.get(url)
            for data in plist["videos"][:limit]:
                tracks.append(
                    Track(
                        id=data["id"],
                        title=data["title"][:25],
                        duration=data["duration"],
                        duration_sec=utils.to_seconds(data["duration"]),
                        thumbnail=data["thumbnails"][-1]["url"].split("?")[0],
                        url=data["link"],
                        channel_name=data["channel"]["name"],
                        user=user,
                        video=video,
                    )
                )
        except:
            pass
        return tracks

    # 🔥 DIRECT STREAM URL (NO DOWNLOAD)
    async def stream(self, video_id: str):
        url = self.base + video_id

        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
        }

        def extract():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info["url"]

        return await asyncio.to_thread(extract)

    # 🔥 DOWNLOAD (API + FALLBACK)
    async def download(self, video_id: str, video: bool = False):
        await self.load_api()

        ext = "mp4" if video else "mp3"
        file_path = f"downloads/{video_id}.{ext}"
        os.makedirs("downloads", exist_ok=True)

        if Path(file_path).exists():
            return file_path

        # 🔥 API DOWNLOAD
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "url": video_id,
                    "type": "video" if video else "audio",
                }

                async with session.get(
                    f"{self.API_URL}/download", params=params
                ) as r:
                    if r.status != 200:
                        raise Exception("API failed")

                    data = await r.json()
                    token = data.get("download_token")

                    stream_url = f"{self.API_URL}/stream/{video_id}?type={'video' if video else 'audio'}"

                    async with session.get(
                        stream_url,
                        headers={"X-Download-Token": token},
                    ) as f:
                        if f.status != 200:
                            raise Exception("Stream failed")

                        with open(file_path, "wb") as out:
                            async for chunk in f.content.iter_chunked(16384):
                                out.write(chunk)

                        logger.info("Downloaded via API")
                        return file_path

        except Exception as e:
            logger.warning(f"API failed: {e}")

        # 🔥 FALLBACK yt-dlp
        try:
            url = self.base + video_id

            ydl_opts = {
                "format": "best" if video else "bestaudio/best",
                "outtmpl": file_path,
                "quiet": True,
                "geo_bypass": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            logger.info("Fallback yt-dlp success")
            return file_path

        except Exception as e:
            logger.error(f"All download failed: {e}")
            return None
