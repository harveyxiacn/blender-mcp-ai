# Blender MCP 贡献指南

感谢你对 Blender MCP 的关注！本指南将帮助你开始贡献。

## 行为准则

请保持尊重和建设性。我们欢迎各经验水平的贡献者。

## 开始

### 1. Fork & Clone

```bash
git clone https://github.com/harveyxiacn/blender-mcp-ai.git
cd blender-mcp-ai
```

### 2. 开发环境设置

```bash
# 安装开发依赖
uv sync --all-extras

# 或使用 pip
pip install -e ".[dev]"
```

### 3. 验证设置

```bash
# 运行测试
pytest

# 检查代码风格
ruff check src/
```

## 项目结构

```
src/blender_mcp/         # MCP 服务器
├── server.py             # 主服务器类
├── connection.py         # Blender TCP 连接
├── skill_manager.py      # 动态 Skill 系统
├── tools_config.py       # 工具 Profile 配置
└── tools/                # MCP 工具模块

addon/blender_mcp_addon/  # Blender 插件
├── executor.py           # 命令调度器
├── handlers/             # Blender API 处理器
├── operators/            # Blender 操作符
└── panels/               # UI 面板
```

## 如何贡献

### 报告 Bug

1. 检查现有 [Issues](https://github.com/harveyxiacn/blender-mcp-ai/issues)
2. 创建新 Issue，包含：
   - Blender 版本
   - Python 版本
   - IDE 和 MCP 客户端
   - 复现步骤
   - 预期行为 vs 实际行为

### 添加新工具

1. **MCP 服务器端**：创建 `src/blender_mcp/tools/my_tool.py`

```python
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

class MyInput(BaseModel):
    param: str = Field(..., description="参数描述")

def register_my_tools(mcp: FastMCP, server) -> None:
    @mcp.tool()
    async def blender_my_action(params: MyInput) -> str:
        """帮助 AI 理解何时使用此工具的描述。"""
        result = await server.execute_command("my_category", "my_action", params.model_dump())
        return str(result)
```

2. **Blender 插件端**：创建 `addon/blender_mcp_addon/handlers/my_handler.py`

```python
import bpy

def handle(action: str, params: dict) -> dict:
    if action == "my_action":
        # 执行 Blender API 调用
        return {"success": True, "result": "完成"}
    return {"success": False, "error": f"未知操作: {action}"}
```

3. **注册**：添加到 `tools_config.py`、`tools/__init__.py`、`executor.py`、`handlers/__init__.py`

4. **添加到 Skill**：如果不是核心工具，在 `skill_manager.py` 中添加到对应 Skill

### 添加新 Skill

编辑 `src/blender_mcp/skill_manager.py`：

```python
SKILL_DEFINITIONS["my_skill"] = SkillInfo(
    name="my_skill",
    description="AI 可理解的清晰描述",
    modules=["my_module_a", "my_module_b"],
    estimated_tools=10,
    workflow_guide="## 工作流指引\n1. 步骤一\n2. 步骤二",
)
```

### 代码风格

- 遵循代码库中的现有模式
- 使用类型提示
- 使用 Pydantic 模型定义工具输入
- 编写描述性的工具 docstring（AI 会读取）
- 工具描述简洁但信息丰富

### 提交信息

使用约定式提交：

```
feat: 添加程序化木纹材质预设
fix: 修正 UV 展开方向
docs: 更新架构文档 Skill 系统部分
refactor: 简化修改器处理器
```

## Pull Request 流程

1. 从 `main` 创建功能分支
2. 完成修改
3. 运行测试：`pytest`
4. 运行检查：`ruff check src/`
5. 如有必要更新文档
6. 提交 PR 并附清晰描述

## 开发技巧

### 热更新

开发时使用插件的热更新功能：
1. 在插件偏好设置中设置开发源代码目录
2. 修改代码后点击 "热更新"
3. 无需重启 Blender

### 测试工具

```bash
# 测试特定工具模块导入
python -c "from blender_mcp.tools.my_tool import register_my_tools; print('OK')"

# 以调试日志运行
python -m blender_mcp --log-level DEBUG
```

### 开发用工具 Profile

开发时在 `tools_config.py` 中设置 `TOOL_PROFILE = "full"` 加载所有工具。生产环境切回 `"skill"`。

## 许可证

贡献代码即表示同意你的贡献以 MIT 许可证授权。

