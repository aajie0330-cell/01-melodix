from fastapi import FastAPI, Request, Response

from app.models.database import get_connection

MAX_LOG_TEXT = 4000


def _clip(text: str) -> str:
    """限制日志长度，避免超大 payload 影响数据库与可读性。"""
    return text[:MAX_LOG_TEXT] if text else ""

def write_api_log(
    *,
    log_type: str,
    request_url: str,
    function_type: str,
    request_method: str,
    request_ip: str,
    message_code: str,
    api_log: str,
    status: str,
    error_message: str | None = None,
    created_by: str = "system",
):
    """写入一条 API 日志到 api_log（请求与响应共用同一张表）。"""
    try:
        conn = get_connection()
        conn.execute(
            """
            INSERT INTO api_log
            (log_type, request_url, function_type, request_method, request_ip,
             message_code, api_log, status, error_message, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                log_type,
                request_url,
                function_type,
                request_method,
                request_ip,
                message_code,
                _clip(api_log),
                status,
                _clip(error_message or ""),
                created_by,
            ),
        )
        conn.commit()
        conn.close()
    except Exception:
        # 日志写入失败不能反向影响主业务接口。
        pass


def write_worker_error(*, endpoint: str, method: str, error: str):
    """记录后台任务错误，避免异步失败无迹可查。"""
    write_api_log(
        log_type="WORKER_ERROR",
        request_url=endpoint,
        function_type=f"{endpoint}:worker",
        request_method=f"BACKGROUND:{method}",
        request_ip="",
        message_code="WORKER_ERROR",
        api_log="",
        status="error",
        error_message=error[:1000],
        created_by="song_worker",
    )


def register_api_logging_middleware(app: FastAPI):
    """注册 API 日志中间件：每次调用都记录 request/response。"""

    @app.middleware("http")
    async def api_logger(request: Request, call_next):
        # 只记录 /api 路径，静态资源不进日志表，减少噪音。
        if not request.url.path.startswith("/api"):
            return await call_next(request)

        request_body = await request.body()

        async def receive():
            return {"type": "http.request", "body": request_body, "more_body": False}

        request = Request(request.scope, receive)
        request_text = request_body.decode("utf-8", errors="replace") if request_body else ""
        request_ip = request.client.host if request.client else ""
        request_url = str(request.url)
        endpoint = request.url.path
        request_method = request.method

        write_api_log(
            log_type="REQUEST",
            request_url=request_url,
            function_type=endpoint,
            request_method=request_method,
            request_ip=request_ip,
            message_code="",
            api_log=request_text,
            status="received",
        )

        try:
            response = await call_next(request)
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk

            # 音频流或大响应不落完整 body，避免日志污染和体积过大。
            content_type = response.headers.get("content-type", "")
            if endpoint.startswith("/api/stream") or "audio/" in content_type:
                response_text = f"[stream response omitted] content_type={content_type}"
            else:
                response_text = response_body.decode("utf-8", errors="replace")
            status_code_text = str(response.status_code)
            write_api_log(
                log_type="RESPONSE",
                request_url=request_url,
                function_type=endpoint,
                request_method=request_method,
                request_ip=request_ip,
                message_code=status_code_text,
                api_log=response_text,
                status="success" if 200 <= response.status_code < 400 else "error",
                error_message="" if 200 <= response.status_code < 400 else response_text[:1000],
            )

            headers = dict(response.headers)
            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=headers,
                media_type=response.media_type,
            )
        except Exception as e:
            write_api_log(
                log_type="RESPONSE",
                request_url=request_url,
                function_type=endpoint,
                request_method=request_method,
                request_ip=request_ip,
                message_code="500",
                api_log="",
                status="error",
                error_message=str(e)[:1000],
            )
            raise
