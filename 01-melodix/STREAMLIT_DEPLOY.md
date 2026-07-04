# Streamlit Cloud 部署指南

## 📋 前提条件
- ✅ GitHub 账号
- ✅ 代码已推送到 GitHub
- ✅ Streamlit Cloud 账号（可用 GitHub 登录）

## 🚀 部署步骤

### 1️⃣ 准备 GitHub 仓库

确保你的代码已经推送到 GitHub：

```bash
git add .
git commit -m "准备部署到 Streamlit Cloud"
git push origin main
```

**重要**: 确保以下文件在仓库根目录：
- ✅ `streamlit_app.py` （主应用文件）
- ✅ `requirements_streamlit.txt` （依赖文件）
- ✅ `.streamlit/config.toml` （配置文件）
- ✅ `app/` 文件夹（包含 `downloader.py` 和 `database.py`）

### 2️⃣ 登录 Streamlit Cloud

1. 访问 [https://share.streamlit.io](https://share.streamlit.io)
2. 点击 **"Sign up"** 或 **"Continue with GitHub"**
3. 授权 Streamlit 访问你的 GitHub 仓库

### 3️⃣ 创建新应用

1. 在 Streamlit Cloud 控制台，点击 **"New app"**
2. 填写以下信息：

| 字段 | 值 | 说明 |
|------|-----|------|
| **Repository** | 选择你的 `01-melodix` 仓库 | 从下拉列表选择 |
| **Branch** | `main` | 或你的默认分支 |
| **Main file path** | `streamlit_app.py` | ⚠️ 重要！ |

### 4️⃣ 高级设置（可选）

点击 **"Advanced settings"** 展开：

#### Python 版本
- 选择 `Python 3.11` 或更高

#### 依赖文件
- 在 **"Requirements file"** 输入: `requirements_streamlit.txt`

#### 环境变量（可选）
如果需要下载受限视频，添加：

| Key | Value |
|-----|-------|
| `YTDLP_COOKIE_BROWSER` | `chrome` 或 `firefox` |

### 5️⃣ 部署

1. 点击底部的 **"Deploy!"** 按钮
2. Streamlit 会自动开始构建和部署
3. 等待 3-5 分钟（首次部署较慢）
4. 看到 "Your app is live!" 表示成功

### 6️⃣ 测试应用

部署成功后：
- 你的应用 URL 会显示在顶部（格式：`https://your-app.streamlit.app`）
- 测试功能：
  - ✅ 添加 YouTube 链接
  - ✅ 下载歌曲
  - ✅ 播放音乐
  - ✅ 删除歌曲

## 🔄 自动部署

之后每次推送到 GitHub，Streamlit 会自动重新部署：

```bash
git add .
git commit -m "更新代码"
git push origin main
```

## ⚠️ 重要提示

### 1. 文件存储限制
- ⚠️ Streamlit Cloud 的文件系统是**临时的**
- 下载的音乐文件会在应用重启后消失
- **建议**: 使用 SQLite 数据库（已配置，数据会持久化）

### 2. 资源限制
- 💾 内存: 1GB
- ⏱️ 执行时间: 无限制
- 🌐 公开访问: 默认所有人可访问

### 3. FFmpeg 依赖
Streamlit Cloud 已预装 FFmpeg，无需额外配置。

### 4. Cookie/登录问题
如果遇到 "Sign in to confirm you're not a bot":
1. 在 Streamlit Cloud 设置中添加环境变量
2. 或使用公开的、不需要登录的 YouTube 视频

### 5. 下载超时
某些长视频可能下载超时，建议：
- 下载短于 10 分钟的视频
- 或在本地运行应用

## 🆓 免费版限制

Streamlit Cloud 免费版：
- ✅ 无限制的公开应用
- ✅ 1GB RAM
- ✅ 1 CPU core
- ⚠️ 文件存储在应用重启后会丢失
- ⚠️ 应用不活跃会休眠

## 📱 分享应用

部署成功后，你可以：
1. 复制应用 URL 分享给朋友
2. 在 GitHub README 中添加链接
3. 设置自定义域名（需要付费版）

## 🐛 常见问题

### Q: 部署失败怎么办？

**A**: 检查日志（Logs）中的错误信息：
- 确保 `requirements_streamlit.txt` 正确
- 确保 `streamlit_app.py` 在根目录
- 确保 Python 版本兼容

### Q: 如何查看日志？

**A**: 在 Streamlit Cloud 控制台：
1. 点击你的应用
2. 点击右上角 **"Manage app"**
3. 选择 **"Logs"** 标签

### Q: 如何删除应用？

**A**: 
1. 进入 **"Manage app"**
2. 点击 **"Settings"**
3. 滚动到底部点击 **"Delete app"**

### Q: 下载的音乐去哪了？

**A**: 存储在 `music/` 文件夹，但会在应用重启后消失。建议：
- 使用数据库记录（已实现）
- 或接入云存储（S3、Cloudinary）

## 📚 其他资源

- [Streamlit 文档](https://docs.streamlit.io/)
- [Streamlit Cloud 文档](https://docs.streamlit.io/streamlit-community-cloud)
- [yt-dlp 文档](https://github.com/yt-dlp/yt-dlp)

## ✅ 部署检查清单

部署前确保：
- [ ] 代码已推送到 GitHub
- [ ] `streamlit_app.py` 在根目录
- [ ] `requirements_streamlit.txt` 在根目录
- [ ] `.streamlit/config.toml` 已创建
- [ ] `app/` 文件夹包含必要模块
- [ ] `.gitignore` 排除了 `music/` 和 `*.db` 文件

---

**部署成功后，你的音乐应用就可以公开访问了！** 🎉
