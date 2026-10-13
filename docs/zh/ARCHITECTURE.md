# Blender MCP 架构设计

## 系统摘要

截至 2026-03-10，仓库当前包含：

- `src/blender_mcp/tools` 下 51 个服务端工具模块
- 源码中 380 个 `@mcp.tool(...)` 注册
- `skill_manager.py` 中 12 个 Skill 分组
- `tools_config.py` 中 6 个加载 Profile

## 运行拓扑

```text
AI 客户端
  -> MCP stdio / streamable-http
Blender MCP 服务端
  -> TCP JSON 消息
Blender 插件
  -> Blender Python API
```

## 主要组件

### MCP 服务端

关键文件：

- `src/blender_mcp/server.py`
- `src/blender_mcp/connection.py`
- `src/blender_mcp/skill_manager.py`
- `src/blender_mcp/tools_config.py`

职责：

- 按 Profile 注册工具
- 维护到 Blender 的 TCP 连接
- 暴露 `list/activate/deactivate` Skill 元工具
- 将 MCP 工具调用转成插件可执行的 `{category, action, params}`

### Blender 插件

关键文件：

- `addon/blender_mcp_addon/__init__.py`
- `addon/blender_mcp_addon/server.py`
- `addon/blender_mcp_addon/executor.py`
- `addon/blender_mcp_addon/handlers/__init__.py`

职责：

- 在 Blender 内运行 socket 服务
- 将命令调度回 Blender 主线程执行
- 按类别路由到具体 handler
- 提供面板、偏好设置和热更新辅助

## Profile 盘点

以下 Profile 数字来自当前工具装饰器的静态统计：

| Profile | 模块数 | 工具数 | 说明 |
|---------|--------|--------|------|
| `minimal` | 4 | 29 | 最小核心操作面 |
| `skill` | 5 | 32 | 核心工具 + 3 个 Skill 元工具 |
| `focused` | 14 | 108 | 静态精选工作集 |
| `standard` | 23 | 165 | 较完整的日常工作集 |
| `extended` | 27 | 194 | 增加物理与批处理 |
| `full` | 50 | 356 | 所有用户可见模块 |

若把 3 个 Skill 元工具单独算入，仓库总计 380 个工具。

## Skill 盘点

| Skill | 预估工具数 | 模块集 |
|-------|------------|--------|
| `modeling` | ~38 | modeling, curves, uv_mapping |
| `materials` | ~17 | material, procedural_materials |
| `style` | ~8 | style_presets, mesh_edit_advanced |
| `character` | ~23 | character_templates, rigging, auto_rig |
| `animation` | ~17 | animation, animation_presets |
| `scene_setup` | ~18 | lighting, camera, world, render |
| `automation` | ~12 | pipeline, quality_audit, style_presets, procedural_materials |
| `physics` | ~18 | physics, constraints |
| `batch_assets` | ~11 | batch, assets |
| `advanced_3d` | ~32 | nodes, compositor, sculpting, texture_painting |
| `sport_character` | ~7 | sport_character |
| `training` | ~11 | training |

## 命令流

1. 客户端调用 MCP 工具。
2. 服务端将工具输入转换为 `{category, action, params}`。
3. `BlenderConnection` 通过 TCP 发送请求。
4. Blender 插件的 socket 服务接收消息。
5. `CommandExecutor` 按类别路由到 handler 模块。
6. handler 执行 Blender API 并返回 JSON。

## 当前执行缺口

2026-03 审查中最重要的架构缺口是：

- `pipeline` 与 `quality_audit` 已在 `src/blender_mcp/tools_config.py` 注册
- `automation` Skill 也会对外暴露这两个模块
- 但 `addon/blender_mcp_addon/handlers/__init__.py` 里还没有这两个类别的映射

结果：

- 这些工具可能会出现在 MCP 工具列表里
- 但真正执行时，插件层仍可能返回未知类别错误

在插件侧完成执行层对齐之前，应把 automation 视为实验性能力。

## 扩展规则

新增工具族时，需要同时更新两层：

1. 服务端工具模块与 `MODULE_REGISTRY`
2. 插件 handler 模块与 handler 注册表
3. Profile / Skill 定义
4. 验证服务端类别与插件类别一致性的测试
