# 桌面应用打包指南

## 📦 打包方案概览

本项目提供**两种独立**的运行模式，互不影响：

### 开发模式（原有功能，完全不变）
- **启动方式**：`start.bat`
- **后端**：`backend/main.py`（端口固定 8099）
- **前端**：Vite 开发服务器（端口 5173）
- **数据目录**：`backend/data/`
- **适用场景**：日常开发、调试

### 桌面应用模式（新增功能）
- **启动方式**：`start_desktop.bat` 或打包后的 exe
- **后端**：`backend/desktop_main.py`（动态端口）
- **前端**：FastAPI 静态文件服务（自动打开浏览器）
- **数据目录**：`%APPDATA%\FileRenamer\`
- **适用场景**：日常使用、分发给其他用户

---

## 🚀 桌面应用模式使用

### 方式一：开发测试（推荐先测试）

```bash
# 1. 确保前端已构建
cd frontend
npm run build
cd ..

# 2. 启动桌面模式
start_desktop.bat
```

**效果：**
- 自动打开浏览器访问应用
- 数据保存在 `%APPDATA%\FileRenamer\`
- 关闭命令行窗口即可停止服务

### 方式二：打包成 exe

```bash
# 1. 运行打包脚本
build_desktop.bat
```

**打包输出：**
- `dist\FileRenamer\FileRenamer.exe`（文件夹模式）
- `dist\FileRenamer.exe`（单文件模式，需修改 spec）

**分发方式：**
- **文件夹模式**：压缩 `dist\FileRenamer\` 为 ZIP 分发
- **单文件模式**：直接分发 `FileRenamer.exe`

---

## 📂 打包配置说明

### Spec 文件

| 文件 | 说明 | 适用场景 |
|------|------|---------|
| `packaging/file_renamer.spec` | 文件夹模式 | 启动更快，便于调试 |
| `packaging/file_renamer_onefile.spec` | 单文件模式 | 分发方便，单个 exe |

**切换模式：**
```bash
# 文件夹模式
pyinstaller packaging\file_renamer.spec

# 单文件模式
pyinstaller packaging\file_renamer_onefile.spec
```

### 自定义配置

#### 修改应用名称
编辑 `backend/desktop_main.py`：
```python
app = FastAPI(
    title="File Renamer - Desktop",
    description="Your Custom Description",
    version="1.0.0",
)
```

#### 修改数据目录
在 `backend/desktop_main.py` 中修改 `get_app_data_dir()` 函数：
```python
def get_app_data_dir() -> Path:
    # 使用程序同目录（便携版）
    return Path(__file__).parent / "data"
```

#### 修改窗口标题
修改 `backend/desktop_main.py`：
```python
print("=" * 50)
print("  Your Custom Title")
print("=" * 50)
```

---

## 🔧 关键技术实现

### 1. 数据目录隔离

桌面模式通过环境变量 `FILERENAMER_DATA_DIR` 切换数据目录：

```python
# backend/services/log_service.py
_data_dir = os.environ.get("FILERENAMER_DATA_DIR")
if _data_dir:
    DB_PATH = Path(_data_dir) / "logs.db"
else:
    DB_PATH = Path(__file__).parent.parent / "data" / "logs.db"
```

**优点：**
- ✅ 开发模式使用 `backend/data/`（版本控制友好）
- ✅ 桌面模式使用 `%APPDATA%\FileRenamer\`（用户可写）
- ✅ 互不干扰，无需修改任何业务逻辑

### 2. 前端静态文件服务

```python
# backend/desktop_main.py
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
```

**效果：**
- 访问 `http://localhost:端口/` → 自动返回 `index.html`
- API 路由仍正常工作（`/api/...`）

### 3. 自动打开浏览器

```python
def open_browser_delayed(url: str, delay: float = 2.0):
    def _open():
        time.sleep(delay)
        webbrowser.open(url)
    threading.Thread(target=_open, daemon=True).start()
```

**延迟原因：**
- 确保 FastAPI 完全启动后再打开浏览器
- 避免用户看到连接错误页面

### 4. 动态端口查找

```python
def find_available_port(start_port=8099, max_attempts=20):
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return port
        except OSError:
            continue
    return 0
```

**优势：**
- 避免 8099 端口被占用导致启动失败
- 支持多实例运行（虽然不建议）

---

## 🧪 测试清单

### 桌面模式测试

- [ ] `start_desktop.bat` 能正常启动
- [ ] 自动打开浏览器
- [ ] 页面能正常显示
- [ ] 文件扫描功能正常
- [ ] 重命名功能正常
- [ ] 设置保存生效（检查 `%APPDATA%\FileRenamer\`）
- [ ] 关闭命令行窗口后服务停止

### 打包测试

- [ ] `build_desktop.bat` 成功构建
- [ ] 打包后的 exe 能正常运行
- [ ] 首次运行能在 `%APPDATA%` 创建数据文件
- [ ] 重命名后的文件能在资源管理器中打开
- [ ] 设置功能正常
- [ ] 日志记录正常

### 兼容性测试

- [ ] Windows 10 测试
- [ ] Windows 11 测试
- [ ] 不同杀毒软件误报测试

---

## ⚠️ 注意事项

### 1. 前端构建

**必须**先构建前端再打包：
```bash
cd frontend
npm run build
cd ..
```

打包脚本已自动包含此步骤，但手动测试时需注意。

### 2. 数据持久化

桌面模式的数据存储在用户目录，**不会被覆盖**：
- 设置：`%APPDATA%\FileRenamer\settings.json`
- 收藏：`%APPDATA%\FileRenamer\favorites.json`
- 日志：`%APPDATA%\FileRenamer\logs.db`

卸载/升级时**不会自动删除**这些数据（符合 Windows 应用规范）。

### 3. 杀毒软件误报

PyInstaller 打包的 exe **可能被误报为病毒**，这是已知问题。

**降低误报的建议：**
- 使用代码签名证书（需购买）
- 添加应用说明文档
- 提供源码供用户自行编译

### 4. UPX 压缩

当前配置**关闭了 UPX 压缩**，原因：
- UPX 压缩的 exe 误报率极高
- 你的项目本身不大（~60MB），无需压缩

如需启用，修改 spec 文件：
```python
upx=True,
```

### 5. 首次启动时间

- **开发模式**：瞬间启动（已加载依赖）
- **桌面模式（文件夹）**：约 3-5 秒
- **单文件模式**：约 5-10 秒（解压时间）

---

## 📊 打包产物大小

| 模式 | 预计大小 | 说明 |
|------|---------|------|
| 开发模式（源代码） | <1MB | 仅代码 |
| 打包（文件夹模式） | ~60MB | 含 Python 运行时 |
| 打包（单文件模式） | ~65MB | 含 Python 运行时 + 临时解压 |

---

## 🐛 常见问题

### Q1: 打包后提示 "Frontend dist not found"
**原因：** 未构建前端或路径错误
**解决：** 先运行 `npm run build`

### Q2: 打包后 exe 启动闪退
**原因：** 可能是杀毒软件拦截或依赖缺失
**解决：**
1. 用命令行启动 exe 查看错误信息
2. 检查杀毒软件日志
3. 尝试关闭 UPX（当前已关闭）

### Q3: 数据没有保存到 %APPDATA%
**原因：** 可能是权限问题
**解决：** 检查 `%APPDATA%\FileRenamer\` 目录是否存在且可写

### Q4: 打包后的 exe 很大
**原因：** 包含 Python 运行时和所有依赖
**解决：** 这是正常现象，无法进一步压缩（除非购买代码签名）

### Q5: 端口被占用
**原因：** 桌面模式使用动态端口，但极端情况可能冲突
**解决：** 修改 `find_available_port()` 的起始端口或尝试次数

---

## 🔄 版本更新

### 方案一：替换 exe（简单粗暴）
- 用户下载新版本 exe
- 覆盖旧版本
- **数据不会丢失**（存储在 %APPDATA%）

### 方案二：增量更新（复杂）
- 检查更新功能
- 下载差异文件
- 需要额外的更新服务

**推荐方案一**，简单可靠。

---

## 📝 后续优化方向

1. **添加应用图标**
   - 准备 `.ico` 文件
   - 修改 spec 文件添加 `icon="assets/icon.ico"`

2. **添加版本信息**
   - 修改 `backend/desktop_main.py` 中的 version 字段
   - 可集成 `file-version` 工具

3. **自动更新检查**
   - 在应用中添加检查更新按钮
   - 下载新版本并提示重启

4. **系统托盘**
   - 最小化到托盘
   - 后台运行
   - 需要额外依赖（如 `pystray`）

5. **安装程序**
   - 使用 Inno Setup 或 NSIS
   - 创建桌面快捷方式
   - 注册卸载信息

---

## ✅ 总结

- ✅ **开发模式完全不变**：`start.bat` 和 `backend/main.py` 无需修改
- ✅ **桌面模式完全独立**：新增文件，互不干扰
- ✅ **数据隔离**：开发/桌面数据分开存储
- ✅ **简单易用**：双击 exe 即可运行
- ✅ **易于维护**：代码结构清晰，配置集中

现在可以开始测试了！
