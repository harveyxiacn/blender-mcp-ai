# Blender MCP 安装指南

## 环境要求

| 项目 | 最低要求 |
|------|----------|
| Python | 3.10 |
| Blender | 4.0 |
| MCP 客户端 | Cursor、Windsurf、Claude Desktop 或兼容实现 |

## 1. 克隆并同步环境

```bash
git clone https://github.com/harveyxiacn/blender-mcp-ai.git
cd blender-mcp-ai
uv sync
```

如需开发依赖：

```bash
uv sync --extra dev
```

## 2. 处理失效的 `.venv`

这个项目经常会被直接拷贝到另一台机器。如果 `.venv/pyvenv.cfg` 里仍然记录旧机器的解释器路径，`uv run` 会在启动前直接失败。

恢复方式：

```bash
rm -rf .venv   # PowerShell: Remove-Item -Recurse -Force .venv
uv sync
```

## 3. 打包或安装 Blender 插件

打包 zip：

```bash
python build_addon.py
```

环境准备好后，也可以尝试自动安装：

```bash
uv run blender-mcp-ai install-addon
```

手动安装步骤：

1. `编辑 -> 偏好设置 -> 插件`
2. 点击 `安装...`
3. 选择 `dist/blender_mcp_addon.zip`
4. 启用 `Blender MCP`
5. 在 3D 视图侧边栏打开 `MCP` 面板

## 4. 配置客户端

示例 `mcp.json`：

```json
{
  "mcpServers": {
    "blender": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/blender-mcp-ai", "blender-mcp-ai"]
    }
  }
}
```

## 5. Tool Profile

以下数字来自 2026-03-10 的代码审查：

| Profile | 模块数 | 启动/可见工具数 | 说明 |
|---------|--------|----------------|------|
| `minimal` | 4 | 29 | 仅核心场景/对象/实用/导出 |
| `skill` | 5 | 32 | 默认配置，含 3 个 Skill 元工具 |
| `focused` | 14 | 108 | 静态精选工具集 |
| `standard` | 23 | 165 | 较完整的日常工作集 |
| `extended` | 27 | 194 | 加入物理与批处理 |
| `full` | 50 | 356 | 全部用户可见模块 |

如果把 3 个 Skill 元工具一起算入，仓库总计是 380 个工具。

## 6. 验证安装

基础检查：

```bash
uv run blender-mcp-ai --version
uv run blender-mcp-ai
```

在 Blender 已启动、插件已启用的情况下检查连接：

```bash
uv run blender-mcp-ai check
```

## 7. 故障排查

| 现象 | 可能原因 | 处理方式 |
|------|----------|----------|
| `uv run` 启动前即失败 | `.venv` 失效 | 删除 `.venv` 后重新 `uv sync` |
| `Connection refused` | 插件未运行 | 启用插件并确认 MCP 面板状态 |
| 工具可见但执行报未知类别 | 服务器与插件执行层不一致 | 暂时不要依赖实验性的 automation 工具 |
| 端口被占用 | 重复实例 | 关闭多余的 Blender 或服务器进程 |
