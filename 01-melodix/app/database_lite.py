"""
简化版数据库模块 - 仅支持 SQLite
适用于 Streamlit Cloud 部署
"""
import sqlite3
from pathlib import Path

# 数据库路径
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "melodix.db"


def get_connection():
    """获取 SQLite 数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def fetchall_dict(query: str, params: tuple = ()):
    """执行查询并返回所有结果（字典列表）"""
    conn = get_connection()
    cur = conn.execute(query, params)
    
    rows = cur.fetchall()
    columns = [c[0] for c in (cur.description or [])]
    
    result = [
        {columns[i]: row[i] for i in range(len(columns))}
        for row in rows
    ]
    
    conn.close()
    return result


def fetchone_dict(query: str, params: tuple = ()):
    """执行查询并返回单个结果（字典）"""
    conn = get_connection()
    cur = conn.execute(query, params)
    
    row = cur.fetchone()
    columns = [c[0] for c in (cur.description or [])]
    
    conn.close()
    
    if not row:
        return None
    
    return {columns[i]: row[i] for i in range(len(columns))}


def execute_sql(query: str, params: tuple = ()):
    """执行 SQL 语句（INSERT/UPDATE/DELETE）"""
    conn = get_connection()
    cur = conn.execute(query, params)
    conn.commit()
    
    rowcount = cur.rowcount
    conn.close()
    
    return rowcount


def init_db():
    """初始化数据库表结构"""
    conn = get_connection()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS songs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        artist TEXT DEFAULT 'Unknown',
        duration INTEGER DEFAULT 0,
        file_path TEXT NOT NULL UNIQUE,
        youtube_url TEXT,
        thumbnail TEXT,
        added_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS playlists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS playlist_songs (
        playlist_id INTEGER,
        song_id INTEGER,
        position INTEGER DEFAULT 0,
        PRIMARY KEY (playlist_id, song_id)
    );

    CREATE TABLE IF NOT EXISTS api_log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        log_type TEXT,
        request_url TEXT,
        function_type TEXT,
        request_method TEXT,
        request_ip TEXT,
        message_code TEXT,
        api_log TEXT,
        status TEXT,
        error_message TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by TEXT
    );
    """)
    conn.commit()
    conn.close()
