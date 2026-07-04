import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# =========================
# CONFIG
# =========================

PROJECT_ROOT = Path(__file__).parent.parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "melodix.db"

DB_ENGINE = os.getenv("DB_ENGINE", "sqlite").strip().lower()

DB_PATH = Path(os.getenv("DB_PATH", str(DEFAULT_DB_PATH)))

DB_HOST = os.getenv("DB_HOST", "")
DB_NAME = os.getenv("DB_NAME", "")

DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")

DB_TRUSTED_CONNECTION = os.getenv("DB_TRUSTED_CONNECTION", "true").lower() == "true"
DB_TRUST_SERVER_CERT = os.getenv("DB_TRUST_SERVER_CERT", "true").lower() == "true"
DB_MDF_PATH = os.getenv("DB_MDF_PATH", "").strip()
DB_LDF_PATH = os.getenv("DB_LDF_PATH", "").strip()


# =========================
# CONNECTION
# =========================

def get_connection():
    # =========================
    # MSSQL MODE (LocalDB / SQL Server)
    # =========================
    if DB_ENGINE == "mssql":
        import pyodbc

        if not DB_NAME:
            raise RuntimeError("DB_NAME is required when DB_ENGINE=mssql")

        base_conn_str = (
            f"Driver={{{DB_DRIVER}}};"
            f"Server={DB_HOST};"
            f"TrustServerCertificate={'yes' if DB_TRUST_SERVER_CERT else 'no'};"
        )

        if DB_TRUSTED_CONNECTION:
            base_conn_str += "Trusted_Connection=yes;"
        else:
            base_conn_str += f"UID={DB_USER};PWD={DB_PASSWORD};"

        def connect(database=None):
            cs = base_conn_str
            if database:
                cs += f"Database={database};"
            return pyodbc.connect(cs)

        # =========================
        # 1. CONNECT MASTER
        # =========================
        conn = connect("master")
        conn.autocommit = True
        cur = conn.cursor()

        # =========================
        # 2. CREATE DATABASE (SAFE MODE - NO MDF / NO ATTACH)
        # =========================
        escaped_db_name = DB_NAME.replace("]", "]]")
        escaped_db_name_literal = DB_NAME.replace("'", "''")

        if DB_MDF_PATH:
            mdf_path = Path(DB_MDF_PATH).expanduser()
            escaped_mdf_path = str(mdf_path).replace("'", "''")
            escaped_ldf_path = DB_LDF_PATH.replace("'", "''")

            if mdf_path.exists():
                try:
                    cur.execute(f"""
                    IF DB_ID(N'{escaped_db_name_literal}') IS NULL
                    BEGIN
                        CREATE DATABASE [{escaped_db_name}]
                        ON (FILENAME = N'{escaped_mdf_path}')
                        FOR ATTACH
                    END
                    """)
                except Exception:
                    # If log file is missing/out-of-sync, SQL Server can rebuild it.
                    cur.execute(f"""
                    IF DB_ID(N'{escaped_db_name_literal}') IS NULL
                    BEGIN
                        CREATE DATABASE [{escaped_db_name}]
                        ON (FILENAME = N'{escaped_mdf_path}')
                        FOR ATTACH_REBUILD_LOG
                    END
                    """)
            else:
                mdf_path.parent.mkdir(parents=True, exist_ok=True)
                if DB_LDF_PATH:
                    cur.execute(f"""
                    IF DB_ID(N'{escaped_db_name_literal}') IS NULL
                    BEGIN
                        CREATE DATABASE [{escaped_db_name}]
                        ON PRIMARY (
                            NAME = N'{escaped_db_name_literal}',
                            FILENAME = N'{escaped_mdf_path}'
                        )
                        LOG ON (
                            NAME = N'{escaped_db_name_literal}_log',
                            FILENAME = N'{escaped_ldf_path}'
                        )
                    END
                    """)
                else:
                    cur.execute(f"""
                    IF DB_ID(N'{escaped_db_name_literal}') IS NULL
                    BEGIN
                        CREATE DATABASE [{escaped_db_name}]
                        ON PRIMARY (
                            NAME = N'{escaped_db_name_literal}',
                            FILENAME = N'{escaped_mdf_path}'
                        )
                    END
                    """)
        else:
            cur.execute(f"""
            IF DB_ID(N'{escaped_db_name_literal}') IS NULL
            BEGIN
                CREATE DATABASE [{escaped_db_name}]
            END
            """)
        conn.commit()

        # =========================
        # 3. FIX LOGIN PERMISSION (IMPORTANT for 18456 / 4060)
        # =========================
        try:
            user_domain = (os.getenv("USERDOMAIN") or "").strip()
            user_name = (os.getenv("USERNAME") or os.getenv("USER") or "").strip()
            login_name = os.getenv("DB_LOGIN", "").strip()

            if not login_name and user_name:
                login_name = f"{user_domain}\\{user_name}" if user_domain else user_name

            login_name = login_name or "sa"
            escaped_login = login_name.replace("]", "]]").replace("'", "''")

            cur.execute(f"""
            USE [{DB_NAME}];

            IF SUSER_ID(N'{escaped_login}') IS NOT NULL
               AND NOT EXISTS (
                SELECT * FROM sys.database_principals
                WHERE name = N'{escaped_login}'
            )
            BEGIN
                CREATE USER [{escaped_login}] FOR LOGIN [{escaped_login}];
                ALTER ROLE db_owner ADD MEMBER [{escaped_login}];
            END
            """)
            conn.commit()
        except Exception:
            # ignore permission issues (LocalDB sometimes restricts this)
            pass

        conn.close()

        # =========================
        # 4. RECONNECT TO TARGET DB
        # =========================
        return connect(DB_NAME)

    # =========================
    # SQLITE MODE
    # =========================
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# QUERY HELPERS
# =========================

def fetchall_dict(query: str, params: tuple = ()):
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
    conn = get_connection()
    cur = conn.execute(query, params)

    row = cur.fetchone()
    columns = [c[0] for c in (cur.description or [])]

    conn.close()

    if not row:
        return None

    return {columns[i]: row[i] for i in range(len(columns))}


def execute_sql(query: str, params: tuple = ()):
    conn = get_connection()
    cur = conn.execute(query, params)
    conn.commit()

    rowcount = cur.rowcount
    conn.close()

    return rowcount


# =========================
# SQLITE INIT
# =========================

def _init_sqlite(conn):
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


# =========================
# MSSQL INIT
# =========================

def _init_mssql(conn):
    conn.execute("""
    IF OBJECT_ID('songs', 'U') IS NULL
    BEGIN
        CREATE TABLE songs (
            id INT IDENTITY(1,1) PRIMARY KEY,
            title VARCHAR(500) NOT NULL,
            artist VARCHAR(200) NULL DEFAULT 'Unknown',
            duration INT NULL DEFAULT 0,
            file_path VARCHAR(1000) NOT NULL UNIQUE,
            youtube_url VARCHAR(1000) NULL,
            thumbnail VARCHAR(1000) NULL,
            added_at DATETIME2(7) NOT NULL DEFAULT SYSUTCDATETIME()
        )
    END
    """)

    conn.execute("""
    IF OBJECT_ID('playlists', 'U') IS NULL
    BEGIN
        CREATE TABLE playlists (
            id INT IDENTITY(1,1) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            created_at DATETIME2(7) NOT NULL DEFAULT SYSUTCDATETIME()
        )
    END
    """)

    conn.execute("""
    IF OBJECT_ID('playlist_songs', 'U') IS NULL
    BEGIN
        CREATE TABLE playlist_songs (
            playlist_id INT NOT NULL,
            song_id INT NOT NULL,
            position INT NULL DEFAULT 0,
            CONSTRAINT PK_playlist_songs PRIMARY KEY (playlist_id, song_id)
        )
    END
    """)

    conn.execute("""
    IF OBJECT_ID('api_log', 'U') IS NULL
    BEGIN
        CREATE TABLE api_log (
            log_id INT IDENTITY(100001,1) PRIMARY KEY,
            log_type VARCHAR(50),
            request_url VARCHAR(500),
            function_type VARCHAR(100),
            request_method VARCHAR(20),
            request_ip VARCHAR(50),
            message_code VARCHAR(50),
            api_log VARCHAR(MAX),
            status VARCHAR(50),
            error_message VARCHAR(1000),
            created_at DATETIME2(7) DEFAULT SYSUTCDATETIME(),
            created_by VARCHAR(100)
        )
    END
    """)


# =========================
# INIT DB ENTRYPOINT
# =========================

def init_db():
    conn = get_connection()

    if DB_ENGINE == "mssql":
        _init_mssql(conn)
    else:
        _init_sqlite(conn)

    conn.commit()
    conn.close()