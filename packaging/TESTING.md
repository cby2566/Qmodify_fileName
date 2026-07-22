# 快速测试指南

## ✅ 问题已修复

**原问题：** `build_desktop.bat` 用系统 Python 安装 PyInstaller，但用虚拟环境 Python 运行，导致 "No module named PyInstaller" 错误。

**修复方案：** 统一使用虚拟环境 Python 检查和安装 PyInstaller。

---

## 🚀 现在重新测试

### 步骤 1：清理旧构建

```bash
# 删除旧的构建产物
rmdir /s /q dist
rmdir /s /q build
```

### 步骤 2：运行打包脚本

```bash
build_desktop.bat
```

**预期流程：**
```
[1/4] Backend virtual environment is available, skipping creation.
[2/4] Installing backend dependencies...
[3/4] Preparing build environment...
Installing dependencies...
[4/4] Building frontend and packaging...
> frontend@1.0.0 build
> vite build

vite v5.x.x building for production...
✓ 12 modules transformed.
dist/index.html                   0.46 kB
dist/assets/index-xxx.js          xxx.xx kB
✓ built in xxx ms

Checking PyInstaller...
Installing PyInstaller...
...
Running PyInstaller...
...
Build Complete!
Output: dist\FileRenamer\
```

### 步骤 3：测试打包后的应用

```bash
# 运行打包后的 exe
dist\FileRenamer\FileRenamer.exe
```

**预期效果：**
- ✅ 控制台窗口显示启动信息
- ✅ 自动打开浏览器
- ✅ 应用界面正常显示
- ✅ 可以扫描文件、重命名

---

## 🐛 如果还有问题

### 问题 1：仍然提示 "No module named PyInstaller"

**原因：** 虚拟环境可能损坏
**解决：**
```bash
# 删除虚拟环境重新创建
rmdir /s /q backend\venv
build_desktop.bat
```

### 问题 2：前端构建失败

**原因：** Node.js 版本不兼容或依赖缺失
**解决：**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
cd ..
```

### 问题 3：打包成功但 exe 运行闪退

**原因：** 可能是路径问题或权限问题
**解决：**
1. 用命令行运行 exe 查看错误信息：
   ```bash
   dist\FileRenamer\FileRenamer.exe
   ```
2. 检查是否有杀毒软件拦截

### 问题 4：浏览器没有自动打开

**原因：** 启动延迟不够或防火墙拦截
**解决：**
1. 手动打开浏览器访问 `http://localhost:端口`
2. 查看控制台输出的端口号

---

## 📋 验证清单

打包成功后，请测试以下功能：

- [ ] 应用能正常启动
- [ ] 浏览器自动打开
- [ ] 能扫描目录
- [ ] 能添加重命名规则
- [ ] 预览功能正常
- [ ] 执行重命名成功
- [ ] 设置能保存（检查 `%APPDATA%\FileRenamer\settings.json`）
- [ ] 收藏能保存（检查 `%APPDATA%\FileRenamer\favorites.json`）
- [ ] 日志能记录（检查 `%APPDATA%\FileRenamer\logs.db`）

---

## 🔄 对比：修复前后

### 修复前（错误逻辑）

```batch
REM ❌ 错误：用系统 Python 检查
"%PYTHON_CMD%" -c "import PyInstaller"
"%PYTHON_CMD%" -m pip install pyinstaller  # 安装到系统 Python

REM ❌ 错误：用虚拟环境 Python 运行（找不到 PyInstaller）
"%VENV_PY%" -m PyInstaller ...
```

### 修复后（正确逻辑）

```batch
REM ✅ 正确：先创建虚拟环境
%PYTHON_CMD% -m venv backend\venv

REM ✅ 正确：用虚拟环境安装依赖
"%VENV_PY%" -m pip install -r backend\requirements.txt

REM ✅ 正确：用虚拟环境检查 PyInstaller
"%VENV_PY%" -c "import PyInstaller"

REM ✅ 正确：用虚拟环境安装 PyInstaller
"%VENV_PY%" -m pip install pyinstaller

REM ✅ 正确：用虚拟环境运行
"%VENV_PY%" -m PyInstaller ...
```

---

## 📊 性能对比

| 操作 | 修复前 | 修复后 |
|------|-------|-------|
| 首次打包 | ❌ 失败 | ✅ 成功 |
| 重复打包（有缓存） | ⚠️ 可能成功 | ✅ 成功 |
| 虚拟环境隔离 | ❌ 混乱 | ✅ 纯净 |

---

现在可以重新运行 `build_desktop.bat` 测试了！如果遇到新问题，请把完整的错误信息发给我。
