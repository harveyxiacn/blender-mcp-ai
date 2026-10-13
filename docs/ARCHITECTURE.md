# Blender MCP 架构设计文档

## 1. 概述

Blender MCP (Model Context Protocol) 是一个允许 AI 助手（如 Claude、GPT 等）通过 IDE（Cursor、Antigravity、Windsurf 等）直接控制 Blender 的系统。通过该系统，AI 可以帮助用户创建 3D 模型、人物角色、动画、场景等。

### 1.1 设计目标

- **跨平台兼容**：支持 Windows、macOS、Linux
- **多 IDE 支持**：支持 Cursor、Antigravity、Windsurf 等支持 MCP 的 IDE
- **功能全面**：覆盖 Blender 核心功能（建模、动画、材质、渲染等）
- **易于扩展**：模块化设计，便于添加新功能
- **实时交互**：支持实时预览和操作反馈

### 1.2 支持的 Blender 版本

- Blender 4.0+
- Blender 5.0+（推荐）

## 2. 系统架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              用户层                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   Cursor    │  │ Antigravity │  │  Windsurf   │  │ 其他 IDE    │    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │
└─────────┼────────────────┼────────────────┼────────────────┼────────────┘
          │                │                │                │
          └────────────────┴────────────────┴────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           MCP 协议层                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Blender MCP Server                            │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │   │
│  │  │  工具注册器  │  │  请求处理器  │  │  响应格式化  │              │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘              │   │
│  │  传输方式：stdio (本地) / HTTP (远程)                            │   │
│  └──────────────────────────────┬──────────────────────────────────┘   │
└─────────────────────────────────┼───────────────────────────────────────┘
                                  │ Socket/HTTP
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          Blender 层                                      │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                   Blender MCP Addon                              │   │
│  │  ┌──────────────────────────────────────────────────────────┐   │   │
│  │  │                    通信服务模块                            │   │   │
│  │  │  Socket Server / HTTP Server                              │   │   │
│  │  └──────────────────────────────────────────────────────────┘   │   │
│  │  ┌──────────────────────────────────────────────────────────┐   │   │
│  │  │                    命令执行引擎                            │   │   │
│  │  │  解析命令 → 验证参数 → 执行操作 → 返回结果               │   │   │
│  │  └──────────────────────────────────────────────────────────┘   │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │   │
│  │  │场景管理 │ │对象操作 │ │ 建模   │ │ 材质   │ │ 动画   │   │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘   │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │   │
│  │  │灯光相机 │ │角色系统 │ │骨骼绑定│ │ 渲染   │ │资产管理 │   │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘   │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │   │
│  │  │ 雕刻   │ │UV/纹理  │ │节点系统│ │合成/VSE │ │ 模拟   │   │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘   │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │   │
│  │  │毛发系统 │ │约束系统 │ │外部集成│ │AI辅助  │ │偏好设置 │   │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     Blender Python API                           │   │
│  │  bpy.data | bpy.ops | bpy.context | bpy.types | bpy.utils       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## 3. 核心组件

### 3.1 MCP Server (blender_mcp)

MCP 服务器是 IDE 和 Blender 之间的桥梁，负责：

- **协议处理**：实现 MCP 协议规范
- **工具注册**：暴露所有可用的 Blender 操作
- **请求转发**：将 AI 的请求转发给 Blender 插件
- **响应格式化**：将 Blender 的响应转换为 MCP 格式

```
blender_mcp/
├── __init__.py           # 包初始化
├── server.py             # MCP 服务器主入口
├── connection.py         # Blender 连接管理
├── tools/                # 工具定义（43个模块，155+工具）
│   ├── __init__.py
│   ├── scene.py          # 场景管理工具
│   ├── object.py         # 对象操作工具
│   ├── modeling.py       # 建模工具
│   ├── material.py       # 材质工具
│   ├── animation.py      # 动画工具
│   ├── lighting.py       # 灯光工具
│   ├── camera.py         # 相机工具
│   ├── character.py      # 角色系统工具
│   ├── rigging.py        # 骨骼绑定工具
│   ├── render.py         # 渲染工具
│   ├── utility.py        # 实用工具
│   ├── export.py         # 导出工具
│   ├── character_template.py  # 角色模板
│   ├── auto_rig.py       # 自动绑定
│   ├── animation_preset.py    # 动画预设
│   ├── physics.py        # 物理模拟
│   ├── scene_advanced.py # 高级场景
│   ├── batch.py          # 批量操作
│   ├── curves.py         # 曲线建模
│   ├── sculpt.py         # 雕刻工具
│   ├── uv.py             # UV映射
│   ├── texture_paint.py  # 纹理绘制
│   ├── nodes.py          # 节点系统
│   ├── compositor.py     # 合成器
│   ├── vse.py            # 视频编辑
│   ├── gpencil.py        # 油笔/2D动画
│   ├── simulation.py     # 高级模拟
│   ├── hair.py           # 毛发系统
│   ├── assets.py         # 资产管理
│   ├── addons.py         # 插件管理
│   ├── world.py          # 世界环境
│   ├── constraints.py    # 约束系统
│   ├── mocap.py          # 动作捕捉
│   ├── preferences.py    # 偏好设置
│   ├── external.py       # 外部集成
│   ├── ai_assist.py      # AI辅助
│   ├── versioning.py     # 版本控制
│   ├── ai_generation.py  # AI生成
│   ├── vr_ar.py          # VR/AR支持
│   ├── substance.py      # Substance集成
│   ├── zbrush.py         # ZBrush集成
│   ├── cloud_render.py   # 云渲染
│   └── collaboration.py  # 实时协作
├── models/               # Pydantic 模型
│   ├── __init__.py
│   ├── common.py         # 通用模型
│   ├── scene.py          # 场景模型
│   ├── object.py         # 对象模型
│   └── animation.py      # 动画模型
└── utils/                # 工具函数
    ├── __init__.py
    ├── validators.py     # 验证器
    └── formatters.py     # 格式化器
```

### 3.2 Blender Addon (blender_mcp_addon)

Blender 插件负责在 Blender 内部执行操作：

- **通信服务**：监听来自 MCP 服务器的连接
- **命令执行**：解析并执行 Blender 操作
- **状态同步**：同步场景状态到 MCP 服务器
- **错误处理**：捕获并报告执行错误

```
blender_mcp_addon/
├── __init__.py           # 插件入口和注册
├── server.py             # 通信服务器
├── executor.py           # 命令执行器
├── handlers/             # 命令处理器（43个模块）
│   ├── __init__.py
│   ├── scene.py          # 场景处理器
│   ├── object.py         # 对象处理器
│   ├── modeling.py       # 建模处理器
│   ├── material.py       # 材质处理器
│   ├── animation.py      # 动画处理器
│   ├── lighting.py       # 灯光处理器
│   ├── camera.py         # 相机处理器
│   ├── character.py      # 角色处理器
│   ├── rigging.py        # 骨骼处理器
│   ├── render.py         # 渲染处理器
│   ├── utility.py        # 实用工具处理器
│   ├── export.py         # 导出处理器
│   ├── character_template.py  # 角色模板处理器
│   ├── auto_rig.py       # 自动绑定处理器
│   ├── animation_preset.py    # 动画预设处理器
│   ├── physics.py        # 物理模拟处理器
│   ├── scene_advanced.py # 高级场景处理器
│   ├── batch.py          # 批量操作处理器
│   ├── curves.py         # 曲线处理器
│   ├── sculpt.py         # 雕刻处理器
│   ├── uv.py             # UV处理器
│   ├── texture_paint.py  # 纹理绘制处理器
│   ├── nodes.py          # 节点处理器
│   ├── compositor.py     # 合成器处理器
│   ├── vse.py            # 视频编辑处理器
│   ├── gpencil.py        # 油笔处理器
│   ├── simulation.py     # 模拟处理器
│   ├── hair.py           # 毛发处理器
│   ├── assets.py         # 资产处理器
│   ├── addons.py         # 插件处理器
│   ├── world.py          # 世界环境处理器
│   ├── constraints.py    # 约束处理器
│   ├── mocap.py          # 动作捕捉处理器
│   ├── preferences.py    # 偏好设置处理器
│   ├── external.py       # 外部集成处理器
│   ├── ai_assist.py      # AI辅助处理器
│   ├── versioning.py     # 版本控制处理器
│   ├── ai_generation.py  # AI生成处理器
│   ├── vr_ar.py          # VR/AR处理器
│   ├── substance.py      # Substance处理器
│   ├── zbrush.py         # ZBrush处理器
│   ├── cloud_render.py   # 云渲染处理器
│   └── collaboration.py  # 协作处理器
├── operators/            # Blender 操作符
│   └── __init__.py
└── panels/               # UI 面板
    └── __init__.py
```

## 4. 通信协议

### 4.1 MCP 服务器 ↔ IDE

使用标准 MCP 协议：
- **传输方式**：stdio（推荐本地使用）或 Streamable HTTP
- **数据格式**：JSON-RPC 2.0

### 4.2 MCP 服务器 ↔ Blender 插件

使用自定义 JSON 协议通过 Socket 通信：

**请求格式：**
```json
{
    "id": "unique-request-id",
    "type": "command",
    "category": "object",
    "action": "create_mesh",
    "params": {
        "name": "Cube",
        "type": "CUBE",
        "location": [0, 0, 0],
        "scale": [1, 1, 1]
    }
}
```

**响应格式：**
```json
{
    "id": "unique-request-id",
    "success": true,
    "data": {
        "object_name": "Cube",
        "object_type": "MESH",
        "vertices_count": 8,
        "faces_count": 6
    },
    "message": "Successfully created mesh object 'Cube'"
}
```

**错误响应：**
```json
{
    "id": "unique-request-id",
    "success": false,
    "error": {
        "code": "INVALID_PARAMS",
        "message": "Invalid mesh type specified",
        "details": "Expected one of: CUBE, SPHERE, CYLINDER, PLANE, TORUS"
    }
}
```

## 5. 功能模块设计

### 5.1 场景管理 (Scene)

| 功能 | 描述 |
|------|------|
| `blender_scene_create` | 创建新场景 |
| `blender_scene_list` | 列出所有场景 |
| `blender_scene_switch` | 切换当前场景 |
| `blender_scene_delete` | 删除场景 |
| `blender_scene_get_info` | 获取场景信息 |
| `blender_scene_set_settings` | 设置场景参数（帧范围、单位等） |

### 5.2 对象操作 (Object)

| 功能 | 描述 |
|------|------|
| `blender_object_create` | 创建基础对象（立方体、球体、圆柱等） |
| `blender_object_delete` | 删除对象 |
| `blender_object_duplicate` | 复制对象 |
| `blender_object_select` | 选择对象 |
| `blender_object_transform` | 变换对象（位置、旋转、缩放） |
| `blender_object_get_info` | 获取对象信息 |
| `blender_object_list` | 列出所有对象 |
| `blender_object_rename` | 重命名对象 |
| `blender_object_parent` | 设置父子关系 |
| `blender_object_join` | 合并对象 |

### 5.3 建模 (Modeling)

| 功能 | 描述 |
|------|------|
| `blender_mesh_edit` | 进入/退出编辑模式 |
| `blender_mesh_extrude` | 挤出操作 |
| `blender_mesh_subdivide` | 细分 |
| `blender_mesh_bevel` | 倒角 |
| `blender_mesh_loop_cut` | 环切 |
| `blender_modifier_add` | 添加修改器 |
| `blender_modifier_apply` | 应用修改器 |
| `blender_modifier_remove` | 移除修改器 |
| `blender_boolean_operation` | 布尔运算 |

### 5.4 材质和纹理 (Material)

| 功能 | 描述 |
|------|------|
| `blender_material_create` | 创建材质 |
| `blender_material_assign` | 分配材质给对象 |
| `blender_material_set_color` | 设置材质颜色 |
| `blender_material_set_properties` | 设置材质属性（金属度、粗糙度等） |
| `blender_material_add_texture` | 添加纹理 |
| `blender_material_node_setup` | 设置节点材质 |
| `blender_material_list` | 列出所有材质 |

### 5.5 灯光 (Lighting)

| 功能 | 描述 |
|------|------|
| `blender_light_create` | 创建灯光（点光、聚光、面光、太阳光） |
| `blender_light_set_properties` | 设置灯光属性（颜色、强度、半径等） |
| `blender_light_delete` | 删除灯光 |
| `blender_hdri_setup` | 设置 HDRI 环境光 |

### 5.6 相机 (Camera)

| 功能 | 描述 |
|------|------|
| `blender_camera_create` | 创建相机 |
| `blender_camera_set_properties` | 设置相机属性（焦距、景深等） |
| `blender_camera_look_at` | 相机朝向目标 |
| `blender_camera_set_active` | 设置活动相机 |
| `blender_camera_orbit` | 环绕动画 |

### 5.7 动画 (Animation)

| 功能 | 描述 |
|------|------|
| `blender_keyframe_insert` | 插入关键帧 |
| `blender_keyframe_delete` | 删除关键帧 |
| `blender_animation_create` | 创建动画动作 |
| `blender_animation_set_interpolation` | 设置插值类型 |
| `blender_timeline_set_range` | 设置时间范围 |
| `blender_timeline_goto_frame` | 跳转到帧 |
| `blender_animation_bake` | 烘焙动画 |

### 5.8 角色系统 (Character)

| 功能 | 描述 |
|------|------|
| `blender_character_create_base` | 创建基础人形网格 |
| `blender_character_add_features` | 添加面部特征 |
| `blender_character_sculpt` | 雕刻调整 |
| `blender_character_add_hair` | 添加头发系统 |
| `blender_character_add_clothing` | 添加服装 |

### 5.9 骨骼绑定 (Rigging)

| 功能 | 描述 |
|------|------|
| `blender_armature_create` | 创建骨架 |
| `blender_bone_add` | 添加骨骼 |
| `blender_armature_generate_rig` | 生成角色绑定 |
| `blender_weight_paint` | 权重绘制 |
| `blender_ik_setup` | 设置 IK 约束 |
| `blender_pose_set` | 设置姿势 |
| `blender_pose_library_add` | 添加到姿势库 |

### 5.10 渲染 (Render)

| 功能 | 描述 |
|------|------|
| `blender_render_settings` | 设置渲染参数 |
| `blender_render_image` | 渲染静态图像 |
| `blender_render_animation` | 渲染动画 |
| `blender_render_preview` | 渲染预览 |
| `blender_compositor_setup` | 设置合成节点 |

## 6. 安全考虑

### 6.1 输入验证

- 所有输入参数通过 Pydantic 模型验证
- 文件路径验证防止目录遍历攻击
- 数值范围检查防止资源耗尽

### 6.2 权限控制

- 文件系统操作限制在指定目录
- 网络访问限制（仅本地 Socket）
- 敏感操作需要确认

### 6.3 错误处理

- 所有异常捕获并转换为友好错误信息
- 不暴露内部实现细节
- 记录错误日志用于调试

## 7. 多 IDE 支持

### 7.1 Cursor

```json
// .cursor/mcp.json
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

### 7.2 Antigravity

```json
// antigravity-mcp.json
{
  "servers": {
    "blender-mcp-ai": {
      "type": "stdio",
      "command": "python -m blender_mcp"
    }
  }
}
```

### 7.3 Windsurf

```json
// .windsurf/mcp-servers.json
{
  "blender": {
    "command": ["python", "-m", "blender_mcp"],
    "transport": "stdio"
  }
}
```

### 7.4 通用配置

对于其他支持 MCP 的 IDE，可使用 HTTP 传输：

```bash
# 启动 HTTP 模式
python -m blender_mcp --transport http --port 8080
```

## 8. 性能优化

### 8.1 连接池

- 复用 Blender 连接
- 支持连接超时和重连

### 8.2 批量操作

- 支持批量命令执行
- 减少通信开销

### 8.3 异步处理

- 长时间操作异步执行
- 支持进度回调

## 9. 扩展性

### 9.1 插件系统

支持通过插件扩展功能：

```python
# 自定义工具示例
from blender_mcp.tools import register_tool

@register_tool("my_custom_tool")
async def my_custom_operation(params: MyToolInput) -> str:
    """自定义操作"""
    # 实现代码
    pass
```

### 9.2 脚本执行

支持执行任意 Blender Python 脚本：

```python
@mcp.tool(name="blender_execute_script")
async def execute_script(params: ScriptInput) -> str:
    """执行 Blender Python 脚本"""
    pass
```

## 10. 版本兼容性

| Blender 版本 | 支持状态 | 备注 |
|-------------|---------|------|
| 2.93 LTS | 部分支持 | 基础功能可用 |
| 3.0 - 3.6 | 支持 | 完整功能 |
| 4.0 - 4.2 | 支持 | 完整功能 |
| 5.0+ | 完全支持 | 推荐版本，支持新特性 |

## 11. 功能实现状态

### 已完成功能 ✅

**基础功能（12个模块）**
- [x] 场景管理（scene）
- [x] 对象操作（object）
- [x] 网格建模（modeling）
- [x] 材质系统（material）
- [x] 灯光系统（lighting）
- [x] 相机系统（camera）
- [x] 动画系统（animation）
- [x] 角色系统（character, character_template）
- [x] 骨骼绑定（rigging, auto_rig）
- [x] 渲染系统（render）
- [x] 实用工具（utility）
- [x] 导出功能（export）

**扩展功能 - 第一批（7个模块）**
- [x] 物理模拟（physics）
- [x] 高级场景（scene_advanced）
- [x] 批量操作（batch）
- [x] 曲线建模（curves）
- [x] 动画预设（animation_preset）

**扩展功能 - 第二批（7个模块）**
- [x] 雕刻工具（sculpt）
- [x] UV映射（uv）
- [x] 纹理绘制（texture_paint）
- [x] 节点系统（nodes）
- [x] 合成器（compositor）
- [x] 视频编辑（vse）
- [x] 油笔/2D动画（gpencil）

**扩展功能 - 第三批（6个模块）**
- [x] 高级模拟（simulation）
- [x] 毛发系统（hair）
- [x] 资产管理（assets）
- [x] 插件管理（addons）
- [x] 世界环境（world）
- [x] 约束系统（constraints）

**扩展功能 - 第四批（4个模块）**
- [x] 动作捕捉（mocap）
- [x] 偏好设置（preferences）
- [x] 外部集成（external）- Unity、Unreal、Godot导出
- [x] AI辅助功能（ai_assist）

**扩展功能 - 第五批（7个模块）**
- [x] 版本控制（versioning）
- [x] AI 生成（ai_generation）- 纹理、材质、参考图
- [x] VR/AR 场景支持（vr_ar）
- [x] Substance 连接（substance）
- [x] ZBrush 连接（zbrush）
- [x] 云渲染集成（cloud_render）
- [x] 实时协作编辑（collaboration）- 简化版

### 未来规划
- [ ] 完整的实时多人协作（WebRTC）
- [ ] AI 模型生成（集成 InstantMesh/TripoSR）
- [ ] 语音控制接口
- [ ] 自然语言场景描述自动生成
- [ ] Houdini 连接
- [ ] Maya 连接
