# 🔧 故障排查指南

## ❌ 问题：installer returned a non-zero exit code

### 症状
```
❗️ installer returned a non-zero exit code
❗️ Error during processing dependencies!
```

### 解决方案

#### 方法 1: 更新依赖文件（推荐）

确保 `requirements_streamlit.txt` 内容为：
```txt
streamlit>=1.28.0
yt-dlp>=2024.8.0
mutagen>=1.47.0
python-dotenv>=1.0.0
```

推送更新：
```bash
git add requirements_streamlit.txt
git commit -m "修复依赖版本"
git push origin main
```

#### 方法 2: 检查配置

在 Streamlit Cloud：
1. 点击 **"Manage app"**
2. 点击 **"Settings"**
3. 确认：
   - **Python version**: `3.11` 或 `3.10`
   - **Requirements file**: `requirements_streamlit.txt`

#### 方法 3: 重启应用

1. 在 Streamlit Cloud 点击 **"Reboot app"**
2. 等待重新部署

#### 方法 4: 查看详细日志

1. 点击 **"Manage app"** → **"Logs"**
2. 查找具体错误信息
3. 根据错误调整依赖

---

## ❌ 问题：ModuleNotFoundError: No module named 'pyodbc'

### 症状
```
ModuleNotFoundError: No module named 'pyodbc'
```

### 解决方案

使用简化版数据库模块：

1. 确保 `app/database_lite.py` 存在
2. 在 `streamlit_app.py` 中使用：
```python
try:
    from app.database_lite import init_db, get_connection, fetchall_dict, fetchone_dict
except ImportError:
    from app.database import init_db, get_connection, fetchall_dict, fetchone_dict
```

3. 推送更新：
```bash
git add .
git commit -m "使用 SQLite 数据库"
git push origin main
```

---

## ❌ 问题：File not found: streamlit_app.py

### 症状
```
Error: Could not find a file at: streamlit_app.py
```

### 解决方案

1. 确保 `streamlit_app.py` 在**根目录**
2. 检查文件名拼写（不是 `streamlit-app.py` 或 `app.py`）
3. 在 Streamlit Cloud 设置中填写正确路径：
   - **Main file path**: `streamlit_app.py`

---

## ❌ 问题：下载失败 "Sign in to confirm you're not a bot"

### 症状
```
❌ 下载失败: Sign in to confirm you're not a bot
```

### 解决方案

#### 方法 1: 设置环境变量

在 Streamlit Cloud：
1. 点击 **"Settings"**
2. 展开 **"Secrets"**
3. 添加：
```toml
YTDLP_COOKIE_BROWSER = "chrome"
```

#### 方法 2: 使用 cookies 文件

1. 导出浏览器 cookies（使用扩展如 "Get cookies.txt"）
2. 在 Streamlit Cloud Secrets 中添加：
```toml
YTDLP_COOKIE_FILE = "/path/to/cookies.txt"
```

#### 方法 3: 只下载公开视频

避免下载需要登录的视频。

---

## ❌ 问题：音乐文件消失

### 症状
下载的音乐在应用重启后消失。

### 原因
Streamlit Cloud 的文件系统是临时的。

### 解决方案

1. **数据库记录会保留**（SQLite 文件会持久化）
2. **音乐文件会丢失**（存储在 `music/` 文件夹）

**建议**：
- 接受这个限制（适合演示）
- 或集成云存储（AWS S3、Cloudinary）

---

## ❌ 问题：应用很慢或超时

### 症状
下载或播放时应用无响应。

### 解决方案

1. **下载短视频**（< 10 分钟）
2. **避免同时下载多个**
3. **等待下载完成**（可能需要 2-5 分钟）

Streamlit Cloud 免费版限制：
- 1GB RAM
- 1 CPU core
- 下载速度受限

---

## ✅ 测试部署是否成功

### 本地测试
```bash
pip install -r requirements_streamlit.txt
streamlit run streamlit_app.py
```

访问 `http://localhost:8501`

### 在线测试步骤

1. ✅ 应用能打开
2. ✅ 可以添加 YouTube URL
3. ✅ 下载成功（等待 2-5 分钟）
4. ✅ 歌曲显示在列表
5. ✅ 可以播放音乐
6. ✅ 可以删除歌曲

---

## 📞 获取帮助

如果问题仍未解决：

1. **查看 Streamlit 论坛**
   https://discuss.streamlit.io/

2. **检查 yt-dlp 问题**
   https://github.com/yt-dlp/yt-dlp/issues

3. **查看完整日志**
   在 Streamlit Cloud: Manage app → Logs

---

## 🔄 快速重置

如果问题无法解决，尝试完全重置：

1. 删除 Streamlit Cloud 上的应用
2. 本地测试确认能运行
3. 重新部署

```bash
# 本地测试
pip install -r requirements_streamlit.txt
streamlit run streamlit_app.py

# 如果本地能运行，推送到 GitHub
git add .
git commit -m "重新部署"
git push origin main
```

然后在 Streamlit Cloud 创建新应用。
