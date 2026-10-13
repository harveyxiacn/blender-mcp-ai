# Contributing to Blender MCP

Thank you for your interest in contributing to Blender MCP! This guide will help you get started.

## Code of Conduct

Be respectful and constructive. We welcome contributors of all experience levels.

## Getting Started

### 1. Fork & Clone

```bash
git clone https://github.com/harveyxiacn/blender-mcp-ai.git
cd blender-mcp-ai
```

### 2. Development Setup

```bash
# Install with dev dependencies
uv sync --all-extras

# Or using pip
pip install -e ".[dev]"
```

### 3. Verify Setup

```bash
# Run tests
pytest

# Check code style
ruff check src/
```

## Project Structure

```
src/blender_mcp/         # MCP Server
├── server.py             # Main server class
├── connection.py         # Blender TCP connection
├── skill_manager.py      # Dynamic skill system
├── tools_config.py       # Tool profile configuration
└── tools/                # MCP tool modules

addon/blender_mcp_addon/  # Blender Addon
├── executor.py           # Command dispatcher
├── handlers/             # Blender API handlers
├── operators/            # Blender operators
└── panels/               # UI panels
```

## How to Contribute

### Reporting Bugs

1. Check existing [Issues](https://github.com/harveyxiacn/blender-mcp-ai/issues)
2. Create a new issue with:
   - Blender version
   - Python version
   - IDE and MCP client
   - Steps to reproduce
   - Expected vs actual behavior

### Adding a New Tool

1. **MCP Server side**: Create `src/blender_mcp/tools/my_tool.py`

```python
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

class MyInput(BaseModel):
    param: str = Field(..., description="Parameter description")

def register_my_tools(mcp: FastMCP, server) -> None:
    @mcp.tool()
    async def blender_my_action(params: MyInput) -> str:
        """Tool description that helps AI understand when to use this tool."""
        result = await server.execute_command("my_category", "my_action", params.model_dump())
        return str(result)
```

2. **Blender Addon side**: Create `addon/blender_mcp_addon/handlers/my_handler.py`

```python
import bpy

def handle(action: str, params: dict) -> dict:
    if action == "my_action":
        # Execute Blender API calls
        return {"success": True, "result": "Done"}
    return {"success": False, "error": f"Unknown action: {action}"}
```

3. **Register**: Add to `tools_config.py`, `tools/__init__.py`, `executor.py`, `handlers/__init__.py`

4. **Add to Skill**: If this is a non-core tool, add the module to a skill in `skill_manager.py`

### Adding a New Skill

Edit `src/blender_mcp/skill_manager.py`:

```python
SKILL_DEFINITIONS["my_skill"] = SkillInfo(
    name="my_skill",
    description="Clear description for AI to understand",
    modules=["my_module_a", "my_module_b"],
    estimated_tools=10,
    workflow_guide="## Workflow Guide\n1. Step one\n2. Step two",
)
```

### Code Style

- Follow existing patterns in the codebase
- Use type hints
- Use Pydantic models for tool inputs
- Write descriptive tool docstrings (AI reads them)
- Keep tool descriptions concise but informative

### Commit Messages

Use conventional commits:

```
feat: add procedural wood material preset
fix: correct UV unwrap orientation
docs: update architecture with skill system
refactor: simplify modifier handler
```

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Run tests: `pytest`
4. Run linter: `ruff check src/`
5. Update documentation if needed
6. Submit PR with clear description

## Development Tips

### Hot Reload

Use the addon's hot reload feature during development:
1. Set Dev Source Path in addon preferences
2. Click "Hot Reload" after code changes
3. No Blender restart needed

### Testing Tools

```bash
# Test a specific tool module imports
python -c "from blender_mcp.tools.my_tool import register_my_tools; print('OK')"

# Test with debug logging
python -m blender_mcp --log-level DEBUG
```

### Tool Profile for Development

Set `TOOL_PROFILE = "full"` in `tools_config.py` during development to load all tools. Switch back to `"skill"` for production.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

