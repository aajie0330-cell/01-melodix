# 🚑 快速修复部署错误

## 你的错误
```
installer returned a non-zero exit code
Error during processing dependencies!
```

## 🔧 立即修复

### 步骤 1: 确认文件

检查这些文件是否存在且正确：

```bash
# 在项目根目录运行
dir streamlit_app.py
dir requirements_streamlit.txt
dir app\database_lite.py
dir .streamlit\config.toml
```

### 步骤 2: 更新并推送

```bash
git add .
git commit -m "修复 Streamlit 部署问题"
git push origin main
```

### 步骤 3: 在 Streamlit Cloud 重启

1. 打开你的应用页面
2. 点击右上角 **"Manage app"**
3. 点击 **"Reboot app"**
4. 等待 3-5 分钟

## ✅ 检查配置

在 Streamlit Cloud，确认这些设置：

| 设置项 | 正确值 |
|--------|--------|
| **Repository** | 你的 GitHub 仓库 |
| **Branch** | `main` |
| **Main file path** | `streamlit_app.py` |
| **Python version** | `3.11` |
| **Requirements file** | `requirements_streamlit.txt` |

## 🧪 本地测试（可选）

如果还是失败，先在本地测试：

```bash
# 安装依赖
pip install -r requirements_streamlit.txt

# 运行应用
streamlit run streamlit_app.py
```

如果本地能运行，说明代码没问题，是部署配置问题。

## 📋 requirements_streamlit.txt 内容

确保文件内容完全一致：

```txt
streamlit>=1.28.0
yt-dlp>=2024.8.0
mutagen>=1.47.0
python-dotenv>=1.0.0
```

**注意**：
- ✅ 使用 `>=` 不是 `==`
- ✅ 没有空行在中间
- ✅ 文件名是 `requirements_streamlit.txt`

## 🆘 如果仍然失败

### 查看详细错误日志

1. 在 Streamlit Cloud 点击 **"Manage app"**
2. 点击 **"Logs"** 标签
3. 滚动到底部查看最新错误
4. 截图或复制错误信息

### 常见原因

#### 原因 1: Python 版本不兼容
**解决**: 在 Settings 中改为 Python 3.11 或 3.10

#### 原因 2: requirements 文件路径错误
**解决**: 确保填写 `requirements_streamlit.txt`（不是 `requirements.txt`）

#### 原因 3: 文件不在根目录
**解决**: 
```bash
# 检查文件位置
git ls-files | grep streamlit_app.py
git ls-files | grep requirements_streamlit.txt
```

应该显示：
```
streamlit_app.py
requirements_streamlit.txt
```

而不是：
```
app/streamlit_app.py  ❌
streaming/streamlit_app.py  ❌
```

## 🔄 完全重置部署

最后的方法：

1. **删除现有应用**
   - 在 Streamlit Cloud: Settings → Delete app

2. **确认本地文件正确**
   ```bash
   git status
   git log -1
   ```

3. **重新推送**
   ```bash
   git push origin main
   ```

4. **重新创建应用**
   - 访问 https://share.streamlit.io
   - 点击 "New app"
   - 重新填写配置

---

## 📞 需要更多帮助？

查看完整的故障排查指南：[TROUBLESHOOT.md](./TROUBLESHOOT.md)
