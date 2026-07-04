from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from app.models.database import get_connection, fetchall_dict, fetchone_dict
from app.downloader import download_audio
from app.helpers.api_logging import write_worker_error

router = APIRouter(prefix="/songs", tags=["songs"])


class AddSongRequest(BaseModel):
    # 前端提交的新增歌曲请求体（目前只需要 YouTube URL）。
    url: str


# 记录进行中的下载任务，让前端可轮询状态。
_download_status: dict[str, dict] = {}


@router.get("")
def list_songs():
    # 返回歌曲列表给前端渲染。
    rows = fetchall_dict(
        "SELECT id, title, artist, duration, youtube_url, thumbnail, added_at "
        "FROM songs ORDER BY added_at DESC"
    )
    return rows


@router.post("")
async def add_song(body: AddSongRequest, background_tasks: BackgroundTasks):
    # 采用后台任务下载，避免请求长时间阻塞。
    url = body.url.strip()
    if not url:
        raise HTTPException(400, "URL is required")

    existing = fetchone_dict("SELECT id FROM songs WHERE youtube_url = ?", (url,))

    if existing:
        raise HTTPException(409, "Song already in library")

    job_id = url
    _download_status[job_id] = {"status": "downloading", "url": url}

    async def _run():
        # 后台执行实际下载与入库逻辑。
        try:
            meta = await download_audio(url)
            conn = get_connection()
            conn.execute(
                "INSERT INTO songs (title, artist, duration, file_path, youtube_url, thumbnail) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (meta["title"], meta["artist"], meta["duration"],
                 meta["file_path"], meta["youtube_url"], meta["thumbnail"])
            )
            conn.commit()
            conn.close()
            _download_status[job_id] = {"status": "done", "title": meta["title"]}
        except Exception as e:
            # 下载或入库失败时，统一写入 API_LOG 便于追查。
            try:
                write_worker_error(endpoint="/api/songs", method="POST", error=str(e))
            except Exception:
                pass
            _download_status[job_id] = {"status": "error", "message": str(e)}

    background_tasks.add_task(_run)
    return {"message": "Download started", "job_id": job_id}


@router.get("/status/{job_id:path}")
def download_status(job_id: str):
    # 查询某个下载任务当前状态（downloading / done / error）。
    status = _download_status.get(job_id)
    if not status:
        raise HTTPException(404, "Job not found")
    return status


@router.delete("/{song_id}")
def delete_song(song_id: int):
    import os
    # 删除时同时处理 DB 与本地文件，保证数据一致性。
    row = fetchone_dict("SELECT file_path FROM songs WHERE id = ?", (song_id,))
    if not row:
        raise HTTPException(404, "Song not found")
    conn = get_connection()
    conn.execute("DELETE FROM songs WHERE id = ?", (song_id,))
    conn.commit()
    conn.close()
    try:
        os.remove(row["file_path"])
    except FileNotFoundError:
        pass
    return {"message": "Deleted"}
