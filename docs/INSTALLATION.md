# Blender MCP 安装指南

## 目录

1. [系统要求](#1-系统要求)
2. [安装 MCP 服务器](#2-安装-mcp-服务器)
3. [安装 Blender 插件](#3-安装-blender-插件)
4. [IDE 配置](#4-ide-配置)
5. [验证安装](#5-验证安装)
6. [故障排除](#6-故障排除)

## 1. 系统要求

### 1.1 软件要求

| 软件 | 最低版本 | 推荐版本 |
|------|---------|---------|
| Python | 3.10 | 3.11+ |
| Blender | 4.0 | 5.0.1 |
| pip | 21.0 | 最新版 |

### 1.2 支持的操作系统

- Windows 10/11 (x64)
- macOS 12+ (Intel/Apple Silicon)
- Linux (Ubuntu 20.04+, Fedora 36+)

### 1.3 支持的 IDE

- Cursor (推荐)
- Antigravity
- Windsurf
- 其他支持 MCP 协议的 IDE

## 2. 安装 MCP 服务器

### 2.1 方式一：通过 pip 安装（推荐）

```bash
# 创建虚拟环境（推荐）
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 安装 blender-mcp-ai
pip install git+https://github.com/harveyxiacn/blender-mcp-ai.git
```

### 2.2 方式二：从源码安装

```bash
# 克隆仓库
git clone https://github.com/your-username/blender-mcp-ai.git
cd blender-mcp-ai

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 安装依赖
pip install -e .
```

### 2.3 方式三：使用 uv（更快）

```bash
# 安装 uv
pip install uv

# 使用 uv 安装
uv pip install git+https://github.com/harveyxiacn/blender-mcp-ai.git

# 或从源码
uv pip install -e .
```

### 2.4 验证 MCP 服务器安装

```bash
# 检查版本
python -m blender_mcp --version

# 显示帮助
python -m blender_mcp --help
```

## 3. 安装 Blender 插件

### 3.1 自动安装（推荐）

安装 MCP 服务器后，运行以下命令自动安装插件：

```bash
python -m blender_mcp install-addon
```

如果需要指定 Blender 路径：

```bash
# Windows
python -m blender_mcp install-addon --blender-path "C:\Program Files\Blender Foundation\Blender 5.0"

# macOS
python -m blender_mcp install-addon --blender-path "/Applications/Blender.app"

# Linux
python -m blender_mcp install-addon --blender-path "/usr/share/blender/5.0"
```

### 3.2 手动安装

1. **下载插件包**
   
   从 GitHub Release 页面下载 `blender_mcp_addon.zip`，或从源码目录获取：
   ```
   blender-mcp-ai/addon/blender_mcp_addon.zip
   ```

2. **在 Blender 中安装**
   
   - 打开 Blender
   - 进入 `编辑` → `偏好设置` → `插件`
   - 点击 `安装...` 按钮
   - 选择下载的 `blender_mcp_addon.zip`
   - 点击 `安装插件`

3. **启用插件**
   
   - 在插件列表中搜索 "MCP"
   - 勾选 `Interface: Blender MCP` 启用插件
   - 点击 `保存偏好设置`

### 3.3 插件设置

启用插件后，在偏好设置中配置：

| 设置项 | 默认值 | 说明 |
|-------|--------|------|
| 服务端口 | 9876 | MCP 通信端口 |
| 自动启动 | 开启 | Blender 启动时自动启动服务 |
| 日志级别 | INFO | 日志详细程度 |

## 4. IDE 配置

### 4.1 Cursor 配置

在项目根目录创建 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "blender": {
      "command": "python",
      "args": ["-m", "blender_mcp"],
      "env": {
        "BLENDER_MCP_HOST": "127.0.0.1",
        "BLENDER_MCP_PORT": "9876"
      }
    }
  }
}
```

或者使用全局配置（Windows）：

```
%APPDATA%\Cursor\User\globalStorage\cursor.mcp\mcp.json
```

macOS:
```
~/Library/Application Support/Cursor/User/globalStorage/cursor.mcp/mcp.json
```

### 4.2 Antigravity 配置

在项目根目录创建 `antigravity-mcp.json`：

```json
{
  "version": "1.0",
  "servers": {
    "blender-mcp-ai": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "blender_mcp"],
      "env": {
        "BLENDER_MCP_HOST": "127.0.0.1",
        "BLENDER_MCP_PORT": "9876"
      }
    }
  }
}
```

### 4.3 Windsurf 配置

在项目根目录创建 `.windsurf/mcp-servers.json`：

```json
{
  "blender": {
    "command": ["python", "-m", "blender_mcp"],
    "transport": "stdio",
    "env": {
      "BLENDER_MCP_HOST": "127.0.0.1",
      "BLENDER_MCP_PORT": "9876"
    }
  }
}
```

### 4.4 通用 HTTP 模式

对于不支持 stdio 的 IDE，可以使用 HTTP 传输模式：

```bash
# 启动 HTTP 服务
python -m blender_mcp --transport http --port 8080
```

然后配置 IDE 连接到 `http://127.0.0.1:8080`

## 5. 验证安装

### 5.1 启动 Blender 并检查插件

1. 打开 Blender
2. 在右侧面板中找到 "MCP" 标签页
3. 检查服务状态显示为 "运行中"

### 5.2 测试连接

在 IDE 中测试 MCP 连接：

```
请帮我在 Blender 中创建一个红色的立方体。
```

如果一切正常，你应该看到：
- Blender 中出现一个红色立方体
- IDE 中显示操作成功的消息

### 5.3 使用 MCP Inspector 测试

```bash
# 安装 MCP Inspector
npm install -g @modelcontextprotocol/inspector

# 测试 MCP 服务器
npx @modelcontextprotocol/inspector python -m blender_mcp
```

## 6. 故障排除

### 6.1 常见问题

#### 问题：MCP 服务器无法启动

**症状**：运行 `python -m blender_mcp` 时出错

**解决方案**：
```bash
# 检查 Python 版本
python --version  # 需要 3.10+

# 重新安装依赖
pip install --upgrade git+https://github.com/harveyxiacn/blender-mcp-ai.git
```

#### 问题：无法连接到 Blender

**症状**：IDE 显示 "无法连接到 Blender"

**解决方案**：
1. 确保 Blender 正在运行
2. 检查插件已启用并显示 "运行中"
3. 检查端口是否被占用：
   ```bash
   # Windows
   netstat -ano | findstr 9876
   
   # macOS/Linux
   lsof -i :9876
   ```
4. 尝试重启 Blender 和 MCP 服务

#### 问题：插件无法启用

**症状**：在 Blender 中启用插件时出错

**解决方案**：
1. 检查 Blender 版本是否兼容（需要 4.0+）
2. 查看 Blender 系统控制台的错误信息
3. 尝试手动安装依赖：
   ```bash
   # 找到 Blender 的 Python 路径
   # Windows: C:\Program Files\Blender Foundation\Blender 5.0\5.0\python\bin\python.exe
   # macOS: /Applications/Blender.app/Contents/Resources/5.0/python/bin/python3.11
   
   # 安装依赖
   <blender-python> -m pip install pydantic
   ```

#### 问题：端口被占用

**症状**：启动时显示 "Address already in use"

**解决方案**：
```bash
# 使用其他端口
python -m blender_mcp --port 9877

# 同时修改 Blender 插件设置中的端口
```

### 6.2 日志位置

**MCP 服务器日志**：
```
# Windows
%USERPROFILE%\.blender-mcp-ai\logs\server.log

# macOS/Linux
~/.blender-mcp-ai/logs/server.log
```

**Blender 插件日志**：
- 查看 Blender 系统控制台（窗口 → 切换系统控制台）
- 或查看：
  ```
  # Windows
  %USERPROFILE%\.blender-mcp-ai\logs\addon.log
  
  # macOS/Linux
  ~/.blender-mcp-ai/logs/addon.log
  ```

### 6.3 获取帮助

如果问题仍未解决：

1. **查看详细日志**：
   ```bash
   python -m blender_mcp --log-level DEBUG
   ```

2. **提交 Issue**：
   访问 [GitHub Issues](https://github.com/your-username/blender-mcp-ai/issues) 并提供：
   - 操作系统版本
   - Blender 版本
   - Python 版本
   - 完整错误日志
   - 复现步骤

3. **社区支持**：
   在 [GitHub Discussions](https://github.com/harveyxiacn/blender-mcp-ai/discussions) 提问

## 下一步

安装完成后，请阅读：
- [快速开始指南](./QUICKSTART.md) - 学习基本操作
- [API 参考](./API_REFERENCE.md) - 查看所有可用功能
- [示例教程](./TUTORIALS.md) - 跟随教程创建项目
