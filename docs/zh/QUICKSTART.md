# Blender MCP 快速开始

## 概览

本指南按 2026-03-10 的仓库状态更新：

- 服务端共 380 个工具、56 个工具模块
- 默认 `skill` Profile 启动 32 个工具
- 共 12 个 Skill 分组可按需激活

## 前置条件

- Blender 4.0+
- Python 3.10+
- `uv`
- 任意兼容 MCP 的客户端，例如 Cursor、Windsurf

## 1. 从源码安装

```bash
git clone https://github.com/harveyxiacn/blender-mcp-ai.git
cd blender-mcp-ai
uv sync
```

如果后续 `uv run` 因 `.venv` 指向失效解释器而报错，删除 `.venv` 后重新执行 `uv sync`。

## 2. 打包并安装 Blender 插件

```bash
python build_addon.py
```

在 Blender 中：

1. 打开 `编辑 -> 偏好设置 -> 插件`
2. 点击 `安装...`
3. 选择 `dist/blender_mcp_addon.zip`
4. 启用 `Blender MCP`
5. 在 3D 视图侧边栏打开 `MCP` 面板

## 3. 配置 MCP 客户端

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

## 4. 启动服务器

```bash
uv run blender-mcp-ai
```

## 5. 第一次会话

先从默认 Profile 可直接工作的请求开始：

```text
列出当前 Blender 场景中的所有对象。
```

然后再尝试按需加载工作流：

```text
激活 materials skill，创建一个球体，并给它分配红色金属材质。
```

## Skill 分组

| Skill | 预估工具数 | 说明 |
|-------|------------|------|
| `modeling` | ~38 | 网格编辑、修改器、曲线、UV |
| `materials` | ~17 | 标准材质与程序化材质 |
| `style` | ~8 | 风格预设、描边、烘焙 |
| `character` | ~23 | 角色模板、绑定、自动绑定 |
| `animation` | ~17 | 关键帧和动画预设 |
| `scene_setup` | ~18 | 灯光、相机、世界、渲染 |
| `automation` | ~12 | 当前仍属实验性，等待插件侧 handler 补齐 |
| `physics` | ~18 | 物理和约束 |
| `batch_assets` | ~11 | 批处理和资产辅助 |
| `advanced_3d` | ~32 | 节点、合成、雕刻、绘制 |
| `sport_character` | ~7 | 运动员角色工作流 |
| `training` | ~11 | 学习与练习引导 |

## 已知限制

- `automation` 目前只是服务器侧工具已暴露，`pipeline` 与 `quality_audit` 还没有接入 Blender 插件 handler 注册表。
- API 参考目前对稳定/核心模块最完整，最新工具盘点请结合项目审查报告查看。

## 下一步

- [INSTALLATION](./INSTALLATION.md)
- [ARCHITECTURE](./ARCHITECTURE.md)
- [API_REFERENCE](./API_REFERENCE.md)
- [ROADMAP](./ROADMAP.md)
- [PROJECT_REVIEW_2026-03](./PROJECT_REVIEW_2026-03.md)
