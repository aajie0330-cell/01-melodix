# Render 部署步骤

## 📋 前提条件
- ✅ GitHub 账号
- ✅ 代码已推送到 GitHub
- ✅ Render 账号（可用 GitHub 登录）

## 🚀 部署步骤

### 1️⃣ 准备 GitHub 仓库
确保你的代码已经推送到 GitHub：

```bash
git add .
git commit -m "准备部署到 Render"
git push origin main
```

### 2️⃣ 登录 Render
1. 访问 [https://render.com](https://render.com)
2. 点击 **"Get Started"** 或 **"Sign Up"**
3. 选择 **"Sign in with GitHub"** 登录

### 3️⃣ 创建新的 Web Service
1. 在 Render Dashboard，点击 **"New +"** 按钮
2. 选择 **"Web Service"**
3. 连接你的 GitHub 仓库：
   - 如果是第一次：点击 **"Connect GitHub"** 授权
   - 找到你的 `01-melodix` 仓库
   - 点击 **"Connect"**

### 4️⃣ 配置部署设置

填写以下信息：

| 字段 | 值 |
|------|-----|
| **Name** | `melodix` 或你喜欢的名字 |
| **Region** | 选择最近的区域（如 Singapore） |
| **Branch** | `main` 或 `master` |
| **Root Directory** | 留空（使用根目录） |
| **Environment** | `Python` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | `Free` (免费版) |

### 5️⃣ 添加环境变量（可选）

如果你有 `.env` 文件中的配置，在 **"Environment Variables"** 部分添加：

点击 **"Add Environment Variable"**，例如：
- `DATABASE_URL` = 你的数据库连接字符串
- `SECRET_KEY` = 你的密钥
- 等等...

⚠️ **注意**: pyodbc 在 Render 上可能有问题，建议使用其他数据库（PostgreSQL、MySQL 等）

### 6️⃣ 部署
1. 点击底部的 **"Create Web Service"**
2. Render 会自动开始构建和部署
3. 等待 5-10 分钟（首次部署较慢）

### 7️⃣ 查看部署状态
- 在 **Logs** 标签可以看到实时日志
- 看到 `Application startup complete` 表示成功
- 你的应用 URL 会显示在顶部（格式：`https://melodix-xxxx.onrender.com`）

## 🔍 测试部署
访问：
- 主页: `https://your-app.onrender.com/`
- 健康检查: `https://your-app.onrender.com/health`
- API 文档: `https://your-app.onrender.com/docs`

## ⚙️ 自动部署
之后每次推送到 GitHub，Render 会自动重新部署：
```bash
git add .
git commit -m "更新代码"
git push origin main
```

## ⚠️ 重要提示

### 数据库问题
你的项目使用 `pyodbc` 连接 SQL Server，但：
- ❌ Render 免费版不支持 SQL Server
- ❌ pyodbc 在 Linux 环境需要额外配置

**解决方案**：
1. **使用 Render 提供的 PostgreSQL**（推荐）
   - 在 Render 创建 PostgreSQL 数据库
   - 修改代码使用 `psycopg2` 或 `sqlalchemy`
   
2. **使用外部数据库**
   - Azure SQL Database
   - AWS RDS
   - 提供连接字符串

3. **使用 SQLite**（开发测试用）
   - 简单但数据会在重启时丢失

### 文件存储问题
- ⚠️ Render 免费版的文件系统是**临时的**
- 下载的音乐文件会在重启后消失
- 建议使用云存储（AWS S3、Cloudinary 等）

## 🆓 免费版限制
- ✅ 每月 750 小时运行时间
- ⚠️ 15 分钟无活动会休眠
- ⚠️ 冷启动需要 30-60 秒
- ❌ 文件存储不持久

## 📚 需要帮助？
- Render 文档: https://render.com/docs
- FastAPI 部署: https://fastapi.tiangolo.com/deployment/

## 🔄 更新检查清单
部署前确保：
- [ ] 代码已提交到 GitHub
- [ ] `requirements.txt` 在根目录
- [ ] 数据库配置正确
- [ ] 环境变量已设置
- [ ] `.gitignore` 包含敏感文件

---

**部署成功后，你的应用会有一个公开 URL，任何人都可以访问！** 🎉
