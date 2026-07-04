from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from app.models.database import fetchone_dict
from pathlib import Path

router = APIRouter(prefix="/stream", tags=["stream"])

CHUNK_SIZE = 1024 * 256  # 256 KB


@router.get("/{song_id}")
async def stream_song(song_id: int, request: Request):
    # 支持分段传输（Range），保证播放器可拖动进度条。
    row = fetchone_dict(
        "SELECT file_path, title FROM songs WHERE id = ?", (song_id,)
    )

    if not row:
        raise HTTPException(404, "Song not found")

    path = Path(row["file_path"])
    if not path.exists():
        raise HTTPException(404, "Audio file missing from server")

    file_size = path.stat().st_size
    range_header = request.headers.get("range")

    if range_header:
        # 处理浏览器传入的字节范围请求，返回 206 Partial Content。
        start, end = 0, file_size - 1
        range_val = range_header.replace("bytes=", "")
        parts = range_val.split("-")
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if parts[1] else file_size - 1
        end = min(end, file_size - 1)
        content_length = end - start + 1

        def iterfile():
            # 按块读取，避免一次性读取大文件导致内存占用过高。
            with open(path, "rb") as f:
                f.seek(start)
                remaining = content_length
                while remaining > 0:
                    chunk = f.read(min(CHUNK_SIZE, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk

        return StreamingResponse(
            iterfile(),
            status_code=206,
            media_type="audio/mpeg",
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(content_length),
            },
        )

    return FileResponse(path, media_type="audio/mpeg", filename=f"{row['title']}.mp3")
