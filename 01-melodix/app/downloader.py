import yt_dlp
import asyncio
import os
from pathlib import Path
from mutagen.mp3 import MP3
from mutagen import File as MutagenFile

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

    # NOTE:
    # Cookie-based mode can trigger YouTube experiment paths that expose only image formats
    # for some accounts/sessions. Keep public-video flow cookieless by default.
    # Re-enable cookie source here only if restricted videos are required.

    return opts


def _get_info(url: str) -> dict:
    # 仅抓取元信息，不执行下载（预留给后续扩展）。
    ydl_opts = {**_base_ydl_opts(), "skip_download": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)


def _download(url: str) -> dict:
    # 下载音频并转为 mp3，返回 yt-dlp 的元数据。
    base_download_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(MUSIC_DIR / "%(id)s.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }
    ydl_opts = {**_base_ydl_opts(), **base_download_opts}

    def _do_extract(opts: dict) -> dict:
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=True)

    try:
        return _do_extract(ydl_opts)
    except Exception as e:
        msg = str(e)
        lowered = msg.lower()
        need_login = "sign in" in lowered or "confirm you're not a bot" in lowered
        no_format = "requested format is not available" in lowered
        sig_fail = "signature solving failed" in lowered or "n challenge solving failed" in lowered

        had_cookie_source = bool(ydl_opts.get("cookiefile") or ydl_opts.get("cookiesfrombrowser"))

        # Some accounts/cookies are placed in YouTube experiments where only image formats are exposed.
        # If that happens, retry once without cookies so public videos can still download.
        if had_cookie_source and (no_format or sig_fail):
            no_cookie_opts = {k: v for k, v in ydl_opts.items() if k not in ("cookiefile", "cookiesfrombrowser")}
            try:
                return _do_extract(no_cookie_opts)
            except Exception:
                pass

        # If no cookie source is configured, auto-try common Windows browsers.
        if need_login and not had_cookie_source:
            for browser in ("edge", "chrome", "firefox"):
                retry_opts = {
                    **ydl_opts,
                    "cookiesfrombrowser": (browser,),
                }
                try:
                    return _do_extract(retry_opts)
                except Exception:
                    continue

        # 把底层报错转换成可读提示，前端可直接显示给用户。
        if need_login and had_cookie_source:
            raise RuntimeError(
                "YouTube requires login/session for this video. "
                "Set YTDLP_COOKIE_BROWSER=chrome (or edge/firefox), "
                "or set YTDLP_COOKIE_FILE to a cookies.txt file."
            ) from e

        ffmpeg_missing = "ffprobe and ffmpeg not found" in lowered or "ffmpeg not found" in lowered
        if ffmpeg_missing:
            # Fallback mode for environments without ffmpeg:
            # keep original audio container (m4a/webm) instead of transcoding to mp3.
            no_ffmpeg_opts = {
                **ydl_opts,
                "postprocessors": [],
                "keepvideo": False,
            }
            return _do_extract(no_ffmpeg_opts)

        raise


async def download_audio(url: str) -> dict:
    # 异步包装同步下载逻辑，避免阻塞主事件循环。
    loop = asyncio.get_event_loop()
    info = await loop.run_in_executor(None, _download, url)

    video_id = info.get("id", "unknown")

    downloaded_path = None
    requested = info.get("requested_downloads") or []
    if requested:
        downloaded_path = requested[0].get("filepath")
    if not downloaded_path:
        downloaded_path = info.get("_filename")

    # Prefer actual downloaded file path; fallback to expected mp3 path.
    resolved_path = Path(downloaded_path) if downloaded_path else (MUSIC_DIR / f"{video_id}.mp3")

    duration = 0
    if resolved_path.exists():
        try:
            # Use generic mutagen parser so non-mp3 fallback files (m4a/webm) are also supported.
            if resolved_path.suffix.lower() == ".mp3":
                audio = MP3(str(resolved_path))
            else:
                audio = MutagenFile(str(resolved_path))
            if audio and getattr(audio, "info", None):
                duration = int(audio.info.length)
            else:
                duration = info.get("duration", 0)
        except Exception:
            duration = info.get("duration", 0)

    title = info.get("title", "Unknown Title")
    uploader = info.get("uploader") or info.get("channel") or "Unknown"
    thumbnail = info.get("thumbnail", "")

    return {
        "title": title,
        "artist": uploader,
        "duration": duration,
        "file_path": str(resolved_path),
        "youtube_url": url,
        "thumbnail": thumbnail,
    }
