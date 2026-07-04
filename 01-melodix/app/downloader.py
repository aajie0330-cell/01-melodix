import yt_dlp
import asyncio
import os
from pathlib import Path
from mutagen.mp3 import MP3

MUSIC_DIR = Path(__file__).parent.parent.parent / "music"
MUSIC_DIR.mkdir(exist_ok=True)


def _base_ydl_opts() -> dict:
    # 统一 yt-dlp 参数：重试、UA、cookies 来源都在这里集中配置。
    opts = {
        "quiet": True,
        "no_warnings": True,
        "retries": 3,
        "extractor_retries": 3,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        },
    }

    # 某些视频需要登录态，优先从 .env 指定的浏览器或 cookie 文件读取会话。
    cookie_file = os.getenv("YTDLP_COOKIE_FILE", "").strip()
    cookie_browser = os.getenv("YTDLP_COOKIE_BROWSER", "").strip()
    if cookie_file:
        opts["cookiefile"] = cookie_file
    elif cookie_browser:
        # Example: chrome, edge, firefox
        opts["cookiesfrombrowser"] = (cookie_browser,)

    return opts


def _get_info(url: str) -> dict:
    # 仅抓取元信息，不执行下载（预留给后续扩展）。
    ydl_opts = {**_base_ydl_opts(), "skip_download": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)


def _download(url: str) -> dict:
    # 下载音频并转为 mp3，返回 yt-dlp 的元数据。
    ydl_opts = {**_base_ydl_opts(), **{
        "format": "bestaudio/best",
        "outtmpl": str(MUSIC_DIR / "%(id)s.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            return info
        except Exception as e:
            msg = str(e)
            lowered = msg.lower()
            if "sign in" in lowered or "confirm you're not a bot" in lowered:
                # 把底层报错转换成可读提示，前端可直接显示给用户。
                raise RuntimeError(
                    "YouTube requires login/session for this video. "
                    "Set YTDLP_COOKIE_BROWSER=chrome (or edge/firefox), "
                    "or set YTDLP_COOKIE_FILE to a cookies.txt file."
                ) from e
            raise


async def download_audio(url: str) -> dict:
    # 异步包装同步下载逻辑，避免阻塞主事件循环。
    loop = asyncio.get_event_loop()
    info = await loop.run_in_executor(None, _download, url)

    video_id = info.get("id", "unknown")
    mp3_path = MUSIC_DIR / f"{video_id}.mp3"

    duration = 0
    if mp3_path.exists():
        try:
            # 优先读取真实 mp3 时长，提升展示准确度。
            audio = MP3(str(mp3_path))
            duration = int(audio.info.length)
        except Exception:
            duration = info.get("duration", 0)

    title = info.get("title", "Unknown Title")
    uploader = info.get("uploader") or info.get("channel") or "Unknown"
    thumbnail = info.get("thumbnail", "")

    return {
        "title": title,
        "artist": uploader,
        "duration": duration,
        "file_path": str(mp3_path),
        "youtube_url": url,
        "thumbnail": thumbnail,
    }
