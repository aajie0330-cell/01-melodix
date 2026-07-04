"""
Melodix - Streamlit 版本
从 YouTube 下载音乐并在浏览器中播放
"""

import streamlit as st
import sqlite3
from pathlib import Path
import asyncio
from datetime import datetime
import os

# 设置页面配置
st.set_page_config(
    page_title="melodix",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 导入自定义模块
from app.downloader import download_audio

# 使用简化版数据库模块（仅 SQLite）
try:
    from app.database_lite import init_db, get_connection, fetchall_dict, fetchone_dict
except ImportError:
    # 本地开发时回退到完整版
    from app.database import init_db, get_connection, fetchall_dict, fetchone_dict

# 初始化数据库
init_db()

# 创建音乐目录
MUSIC_DIR = Path("music")
MUSIC_DIR.mkdir(exist_ok=True)


def format_duration(seconds):
    """格式化时长为 MM:SS"""
    if not seconds:
        return "0:00"
    mins = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{mins}:{secs:02d}"


def get_all_songs():
    """获取所有歌曲"""
    return fetchall_dict(
        "SELECT id, title, artist, duration, youtube_url, thumbnail, added_at "
        "FROM songs ORDER BY added_at DESC"
    )


def delete_song_by_id(song_id):
    """删除歌曲"""
    row = fetchone_dict("SELECT file_path FROM songs WHERE id = ?", (song_id,))
    if row:
        conn = get_connection()
        conn.execute("DELETE FROM songs WHERE id = ?", (song_id,))
        conn.commit()
        conn.close()
        
        # 删除文件
        try:
            file_path = Path(row["file_path"])
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            st.warning(f"文件删除失败: {e}")
        
        return True
    return False


def add_custom_css():
    """添加自定义样式"""
    st.markdown("""
    <style>
        /* 主题色 */
        :root {
            --primary: #6366f1;
            --bg-dark: #0f1419;
        }
        
        /* 隐藏 Streamlit 默认元素 */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* 卡片样式 */
        .song-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 12px;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .song-title {
            font-size: 1.2rem;
            font-weight: 600;
            color: white;
            margin-bottom: 0.5rem;
        }
        
        .song-artist {
            font-size: 0.9rem;
            color: rgba(255,255,255,0.8);
            margin-bottom: 0.5rem;
        }
        
        .song-duration {
            font-size: 0.85rem;
            color: rgba(255,255,255,0.6);
        }
        
        /* 按钮样式 */
        .stButton > button {
            width: 100%;
            border-radius: 8px;
            font-weight: 500;
        }
        
        /* 输入框样式 */
        .stTextInput > div > div > input {
            border-radius: 8px;
        }
        
        /* 标题样式 */
        h1 {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
    </style>
    """, unsafe_allow_html=True)


# ============================================
# 主应用
# ============================================

def main():
    add_custom_css()
    
    # 标题
    st.markdown("# 🎵 melodix")
    st.markdown("*从 YouTube 下载音乐并在线播放*")
    st.markdown("---")
    
    # 侧边栏
    with st.sidebar:
        st.markdown("## 📚 音乐库")
        
        # 视图选择
        view = st.radio(
            "选择视图",
            ["所有歌曲", "收藏", "最近播放"],
            label_visibility="collapsed"
        )
        
        # 统计信息
        songs = get_all_songs()
        st.markdown("---")
        st.metric("歌曲总数", len(songs))
        
        # 关于
        st.markdown("---")
        st.markdown("""
        ### 关于
        **melodix** 是一个简单的音乐下载和播放应用。
        
        #### 功能
        - 🔗 从 YouTube 下载音乐
        - 🎧 在线播放
        - 📝 查看歌曲列表
        - 🗑️ 删除歌曲
        
        #### 使用方法
        1. 在输入框中粘贴 YouTube URL
        2. 点击"下载歌曲"
        3. 等待下载完成
        4. 在列表中播放
        """)
    
    # 主内容区
    tab1, tab2 = st.tabs(["🎵 播放器", "➕ 添加歌曲"])
    
    with tab2:
        st.markdown("### 添加新歌曲")
        
        col1, col2 = st.columns([4, 1])
        
        with col1:
            url = st.text_input(
                "YouTube URL",
                placeholder="粘贴 YouTube 链接...",
                label_visibility="collapsed",
                key="youtube_url"
            )
        
        with col2:
            download_btn = st.button("下载歌曲", type="primary", use_container_width=True)
        
        if download_btn:
            if not url or not url.strip():
                st.error("❌ 请输入 YouTube URL")
            else:
                # 检查是否已存在
                existing = fetchone_dict("SELECT id FROM songs WHERE youtube_url = ?", (url,))
                
                if existing:
                    st.warning("⚠️ 该歌曲已在音乐库中")
                else:
                    with st.spinner("⏳ 正在下载...这可能需要几分钟"):
                        try:
                            # 执行异步下载
                            meta = asyncio.run(download_audio(url))
                            
                            # 保存到数据库
                            conn = get_connection()
                            conn.execute(
                                "INSERT INTO songs (title, artist, duration, file_path, youtube_url, thumbnail) "
                                "VALUES (?, ?, ?, ?, ?, ?)",
                                (meta["title"], meta["artist"], meta["duration"],
                                 meta["file_path"], meta["youtube_url"], meta["thumbnail"])
                            )
                            conn.commit()
                            conn.close()
                            
                            st.success(f"✅ 下载成功: {meta['title']}")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ 下载失败: {str(e)}")
                            
                            # 显示详细错误信息
                            if "sign in" in str(e).lower() or "bot" in str(e).lower():
                                st.info("""
                                **提示**: 该视频可能需要登录才能下载。
                                
                                解决方法：
                                1. 创建 `.env` 文件
                                2. 添加: `YTDLP_COOKIE_BROWSER=chrome`
                                3. 或使用 Firefox: `YTDLP_COOKIE_BROWSER=firefox`
                                """)
        
        st.markdown("---")
        st.markdown("""
        #### 📌 支持的网站
        - YouTube
        - YouTube Music
        - 等等...
        
        #### ⚙️ 设置（可选）
        如果下载受限视频，创建 `.env` 文件并添加：
        ```
        YTDLP_COOKIE_BROWSER=chrome
        ```
        """)
    
    with tab1:
        st.markdown("### 🎵 音乐列表")
        
        # 刷新按钮
        if st.button("🔄 刷新列表", use_container_width=True):
            st.rerun()
        
        songs = get_all_songs()
        
        if not songs:
            st.info("📭 音乐库为空，请先添加歌曲")
        else:
            # 搜索框
            search = st.text_input("🔍 搜索", placeholder="搜索歌曲或艺术家...", label_visibility="collapsed")
            
            # 过滤歌曲
            if search:
                songs = [
                    s for s in songs 
                    if search.lower() in s["title"].lower() or search.lower() in s["artist"].lower()
                ]
            
            st.markdown(f"*找到 {len(songs)} 首歌曲*")
            st.markdown("---")
            
            # 显示歌曲列表
            for idx, song in enumerate(songs, 1):
                with st.container():
                    col1, col2, col3 = st.columns([0.5, 5, 1])
                    
                    with col1:
                        st.markdown(f"**{idx}**")
                    
                    with col2:
                        st.markdown(f"""
                        <div class="song-card">
                            <div class="song-title">{song['title']}</div>
                            <div class="song-artist">🎤 {song['artist']}</div>
                            <div class="song-duration">⏱️ {format_duration(song['duration'])}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col3:
                        # 播放按钮
                        file_path = Path(song["file_path"])
                        if file_path.exists():
                            with open(file_path, "rb") as audio_file:
                                audio_bytes = audio_file.read()
                                st.audio(audio_bytes, format="audio/mp3")
                        
                        # 删除按钮
                        if st.button("🗑️", key=f"del_{song['id']}", help="删除歌曲"):
                            if delete_song_by_id(song["id"]):
                                st.success("✅ 已删除")
                                st.rerun()
                            else:
                                st.error("❌ 删除失败")
                    
                    st.markdown("---")


if __name__ == "__main__":
    main()
