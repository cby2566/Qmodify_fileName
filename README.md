# 文件批量重命名工具

一个用于批量重命名文件的本地工具，提供可视化界面和丰富的重命名规则。

---

## 目录

- [功能特性](#功能特性)
- [环境要求](#环境要求)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [使用说明](#使用说明)
- [模板重组](#模板重组)
- [项目结构](#项目结构)
- [配置](#配置)
- [常见问题](#常见问题)
- [开发注意事项](#开发注意事项)
- [许可](#许可)

---

## 功能特性

| 特性 | 说明 |
|------|------|
| 📁 目录扫描 | 支持递归扫描，自动识别目标类型文件 |
| 🧭 增强路径输入 | 支持常用目录、历史扫描路径、本机目录补全和路径有效性校验 |
| 🔍 多条件筛选 | 扩展名、大小、日期、正则、关键词 |
| 🏷️ 扩展名池管理 | 动态管理可选扩展名池，支持添加 / 删除并自动持久化到后端 |
| 🔤 正则提取 | 支持命名捕获组，按组折叠展示 |
| 📋 规则叠加 | 前缀、后缀、插入、替换、序号、模板重组 |
| 👁️ 实时预览 | 冲突检测、状态高亮 |
| 🛠️ 文件操作 | 可用配置的软件打开文件，也可仅从当前列表移除文件 |
| ↩️ 撤销回滚 | 操作批次管理，一键撤销 |
| 📜 操作日志 | SQLite 持久化，支持筛选和导出 |
| ⭐ 正则收藏夹 | 常用正则保存复用 |
| 🧩 可调侧边栏 | 侧边栏支持拖拽调宽、手动展开/收起并记忆状态 |
| 📤 数据导出 | CSV / TXT 格式 |


## 环境要求

| 工具 | 版本 | 说明 |
|------|------|------|
| Python | ≥ 3.10 | 后端运行时（推荐 3.10+，项目基于 3.13 开发） |
| Node.js | ≥ 18 | 前端运行时（项目基于 v20.19 开发） |
| npm | ≥ 9 | Node.js 包管理器（项目基于 10.8 开发） |
| pip | ≥ 22 | Python 包管理器 |

> 以上为最低要求版本，使用更新版本通常也能正常运行。


## 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 后端 | Python · FastAPI · Pydantic · Uvicorn | ≥ 3.10 · 0.115 · 2.9 · 0.30 |
| 前端 | Vue 3 · Vite · Element Plus · Pinia | ^3.4 · ^5.4 · ^2.8 · ^2.2 |


## 快速开始

### 方式一：一键启动（推荐）

```bash
start.bat
```

脚本会自动完成：创建虚拟环境 → 安装后端 pip 依赖 → 安装前端 npm 依赖 → 启动两个服务。

> ⚠️ **注意**：start.bat 内部使用 start 弹出新窗口。如果在某些环境下窗口被隐藏或一闪而过，请改用下面的手动启动方式。

### 方式二：手动启动（备用）

**终端 1 — 后端：**

```bash
cd backend
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8099
```

如果是在 PowerShell 中已激活的环境（目前在用的方式）：

```powershell
.\\venv\\Scripts\\Activate.ps1
uvicorn main:app --reload --port 8099
```

**终端 2 — 前端：**

```bash
cd frontend
npm install
npm run dev
```

启动后访问 http://localhost:5173

## 使用说明

1. 打开浏览器访问 http://localhost:5173
2. 在路径输入框中输入或选择要扫描的目录，点击「扫描」
3. 使用筛选条件过滤文件，或在文件表格中点击「打开」「删除」处理单个条目
4. 添加重命名规则，实时预览效果
5. 确认无误后点击「执行重命名」
6. 可在「日志」面板查看历史操作并撤销

### 路径输入与扫描

- 路径输入框支持常用目录、历史扫描路径和本机目录自动补全
- 成功执行「扫描」后，路径会自动保存到浏览器本地历史记录，下次刷新页面后仍可选择
- 输入路径后会自动校验目录是否存在，路径无效时不会继续扫描
- 顶部路径输入框会根据窗口宽度自动伸缩，窄窗口下会换行显示

### 文件表格操作

- 「打开」会根据设置中的「打开方式」调用指定软件打开文件；未配置时使用系统默认方式打开
- 「删除」只会把文件从当前列表中移除，不会删除磁盘上的真实文件

### 侧边栏布局

- 左侧侧边栏默认宽度为 360px
- 可拖动侧边栏右侧分隔条调整宽度，范围为 280px 到 520px
- 标题左侧按钮可手动打开或关闭侧边栏
- 侧边栏宽度和展开/收起状态会保存在浏览器本地，下次打开自动恢复

## 模板重组

模板重组功能允许你通过正则表达式从原文件名中提取字段，再用模板重新排列组合。

### 示例场景

**原始文件：**

`
[幻樱字幕组] 海贼王 第001集 [720P].ass
[幻樱字幕组] 海贼王 第002集 [720P].ass
[喵喵字幕组] 火影忍者 第001集 [1080P].ass
`

**目标格式：**

`
海贼王 - 第001集 [720P] [幻樱字幕组].ass
`

### 操作步骤

1. 扫描目录，选中要处理的文件
2. 在「正则表达式」输入框填写提取规则（用于从原文件名中提取命名分组）：

`
^\\[(?P<group>.+?)\\]\\s*(?P<anime>.+?)\\s+(?P<episode>.+?)\\[(?P<quality>.+?)\\]$
`

点击「验证」确认正则有效

3. 点击「添加规则」→「模板重组」
4. 在模板输入框填写目标格式：

`
{anime} - {episode} [{quality}] [{group}]
`

可用字段：
- 正则中提取的命名分组（如 {group} {anime} {episode} {quality}）
- 内置字段：{__stem__}（原文件名主干）、{__index__}（文件序号，从 1 开始）

5. 点击「刷新预览」，确认新文件名符合预期
6. 点击「执行重命名」

### 注意事项

- 如果某个文件不匹配正则，模板中引用的字段会缺失，该文件将保持原名不变
- 模板重组通常需要配合正则表达式使用，单独使用模板只能访问 {__stem__} 和 {__index__}

## 项目结构

```
Qmodify_fileName/
├── backend/          # FastAPI 后端
│   ├── routers/      # API 路由
│   ├── services/     # 业务逻辑
│   ├── models/       # 数据模型
│   └── data/         # 持久化数据
├── frontend/         # Vue 3 前端
│   └── src/
│       ├── components/  # 组件
│       ├── stores/   # 状态管理
│       ├── api/      # API 调用
│       └── utils/    # 工具函数
├── start.bat         # Windows 一键启动脚本
└── README.md
```

---

---

## 配置

在「设置」面板中可配置：

| 配置项 | 说明 |
|--------|------|
| 可选扩展名池 | 动态维护可选扩展名列表，新增 / 删除即时生效并持久化 |
| 当前目标扩展名 | 从池中勾选本次实际扫描的目标类型；与池自动保持同步 |
| 默认是否递归扫描 | 控制扫描是否进入子目录 |
| 最大扫描深度 | 限制递归层数 |
| 打开方式 | 配置点击「打开」时使用的软件路径；留空则使用系统默认打开方式 |
| 日志保留天数 | 自动清理过期日志 |
| 预览防抖延迟 | 控制实时预览的触发频率 |

---

## 常见问题

### 1. 前端启动报错 Failed to parse source for import analysis

**错误信息示例**：

```
[plugin:vite:import-analysis] Failed to parse source for import analysis because the content contains invalid JS syntax.
```

**原因**：源文件被以 **UTF-8 with BOM** 编码保存。Vite 解析 JS/JSON 时无法处理 BOM 头（字节 EF BB BF）。

**常见诱因**：
- 使用 PowerShell `Set-Content -Encoding UTF8` 写入文件（Windows PowerShell 会自动添加 BOM）
- 使用某些编辑器保存时默认勾选了 "添加 BOM" 选项

**解决**：将所有前端源文件保存为 **UTF-8 无 BOM** 格式。

批量检测并移除 BOM 的 PowerShell 脚本：

```powershell
$files = Get-ChildItem -Path "frontend\src" -Recurse -Include *.js,*.vue
foreach ($f in $files) {
    $bytes = [System.IO.File]::ReadAllBytes($f.FullName)
    if ($bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
        $content = $bytes[3..($bytes.Length-1)]
        [System.IO.File]::WriteAllBytes($f.FullName, $content)
        Write-Output "Fixed: $($f.Name)"
    }
}
```

或使用 Node.js 批量修复：

```javascript
const fs = require("fs");
const path = require("path");

function fixBOM(dir) {
  fs.readdirSync(dir).forEach(entry => {
    const full = path.join(dir, entry);
    if (fs.statSync(full).isDirectory()) { fixBOM(full); return; }
    const buf = fs.readFileSync(full);
    if (buf[0] === 0xEF && buf[1] === 0xBB && buf[2] === 0xBF) {
      fs.writeFileSync(full, buf.subarray(3));
      console.log("Fixed:", entry);
    }
  });
}
fixBOM("frontend/src");
```

### 2. 端口被占用

如果 8099 或 5173 已被占用：

```powershell
# 查看占用进程
Get-NetTCPConnection -LocalPort 8099 -ErrorAction SilentlyContinue
Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue

# 结束进程（替换为实际的 OwningProcess）
Stop-Process -Id <PID> -Force
```
---

## 开发注意事项

### 文件编码

- 前端所有源文件（.js / .vue / .json）统一使用 **UTF-8 无 BOM** 编码
- PowerShell `Set-Content -Encoding UTF8` 会自动添加 BOM，导致 Vite 解析失败
- 推荐使用 Node.js 或 VS Code 修改文件（默认无 BOM）

### 前后端字段映射

前端规则对象使用 `type` 字段，后端 Pydantic 模型使用 `rule_type`。`api/index.js` 中的 `transformRuleForBackend` 函数负责转换：

- `type` → `rule_type`
- 序列号规则的 `position` → `sequence_position`（同时删除原 `position` 字段，避免 Pydantic 校验冲突）

### 后端数据流

`/api/rename/preview` 接口接收 Pydantic 模型对象后，需用 `model_dump(exclude_none=True)` 转为字典再传入 `rename_service.apply_rules()`，因为该函数使用 `dict.get()` 方法访问字段，Pydantic 模型对象不支持此方法。

### Vue 组件 prop 传递

子组件不应直接修改 props。RuleItem.vue 中的复选框使用 `:checked` 只读绑定 + `@change` 事件通知父组件切换状态，而非 `v-model` 双向绑定直接修改 prop。

### 表格选中状态同步

el-table 的 `@selection-change` 事件返回的是当前全部选中项数组，应直接赋值给 store（`selectedFiles = selected`），而非遍历 push（会导致取消选中无法同步）。

---

## 许可

个人使用
