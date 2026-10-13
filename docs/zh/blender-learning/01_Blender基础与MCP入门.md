# 01_Blender基础与MCP入门

欢迎来到 Blender 与 AI 协作的奇妙世界！本教程将带你从零开始，了解如何通过 MCP（Model Context Protocol）协议，让 AI 成为你的 3D 创作助手。

---

## 1. Blender 简介

### 什么是 Blender？
Blender 是一款开源、免费且功能极其强大的全流程 3D 创作套件。它不仅支持建模、动画、渲染，还涵盖了合成、运动跟踪、视频编辑甚至 2D 动画制作。

### 主要应用领域
- **3D 建模与雕刻**：创建角色、场景和道具。
- **动画制作**：从简单的关键帧动画到复杂的角色骨骼动画。
- **视觉特效 (VFX)**：电影级的特效合成。
- **游戏开发**：为游戏引擎（如 Unity, Unreal）提供素材。
- **科学可视化**：将复杂数据转化为直观的 3D 模型。

### 为什么选择 Blender 5.0？
Blender 5.0 带来了更强大的渲染引擎（Cycles/Eevee）、更智能的几何节点（Geometry Nodes）以及对 AI 协作的深度支持。

---

## 2. MCP 协议基础

### 什么是 MCP？
MCP（Model Context Protocol）是一种开放协议，它允许 AI 模型（如 Claude, GPT）安全地访问本地工具和数据。

### AI 控制架构
在 `blender-mcp-ai` 项目中，架构如下：
1. **用户**：向 AI 发出自然语言指令（例如：“创建一个红色的立方体”）。
2. **AI (LLM)**：理解指令，并决定调用哪个 MCP 工具。
3. **MCP Server**：接收 AI 的请求，并将其转化为 Blender 能够理解的 Python 代码。
4. **Blender**：执行代码，在 3D 场景中生成结果。

这种架构让你无需学习复杂的 Python API，只需通过对话即可完成 3D 创作。

---

## 3. 环境设置与第一个场景

### 准备工作
1. 确保已安装 **Blender 5.0**。
2. 启动 `blender-mcp-ai` 服务（请参考项目根目录的安装指南）。

### 连接测试
你可以尝试向 AI 发送以下指令来检查连接是否正常：
> "请列出当前 Blender 中的所有场景。"

AI 应该会调用 `blender_scene_list` 工具并返回结果。

### 创建你的第一个场景
指令示例：
> "创建一个名为 'MyFirstScene' 的新场景。"

**AI 内部操作：**
```json
// AI 调用工具示例
{
  "tool": "blender_scene_create",
  "arguments": {
    "name": "MyFirstScene"
  }
}
```

---

## 4. 核心概念速览

在开始创作前，你需要了解几个关键概念：

- **对象 (Object) vs 网格 (Mesh)**：
  - **对象**是场景中的一个实体，包含位置、旋转和缩放信息。
  - **网格**是对象的几何形状数据（点、线、面）。
- **场景 (Scene) vs 世界 (World)**：
  - **场景**包含所有的物体、灯光和摄像机。
  - **世界**定义了背景环境、光照和雾效。
- **数据块 (Data Blocks)**：
  - Blender 采用模块化管理，材质、纹理、网格都是独立的数据块，可以被多个对象共享。

---

## 5. MCP 工具基础

为了高效控制 Blender，AI 使用了一系列专门的工具。

### 常用工具列表
- `blender_get_info`: 获取 Blender 的版本、渲染引擎等基本信息。
- `blender_scene_create`: 创建新场景。
- `blender_scene_list`: 列出所有场景。
- `blender_object_create`: 创建几何体（如立方体、球体）。
- `blender_object_delete`: 删除指定的对象。

### 技能系统 (Skill System)
AI 不仅仅是调用单个工具，它还能组合多个工具完成复杂任务。例如，“创建一个桌子”可能涉及多次调用 `blender_object_create` 并调整它们的位置。

---

## 6. 实践练习

### 练习 1：环境检查
**任务**：获取当前 Blender 的版本信息。
**指令**："告诉我你现在连接的 Blender 版本是多少？"
**预期结果**：AI 调用 `blender_get_info` 并告诉你版本号（应为 5.0.x）。

### 练习 2：基础建模
**任务**：在场景中创建一个立方体并将其命名为 "Base_Cube"。
**指令**："在当前场景创建一个立方体，名字叫 Base_Cube。"
**预期结果**：AI 调用 `blender_object_create`，参数 `type='MESH_CUBE'`, `name='Base_Cube'`。

### 练习 3：场景清理
**任务**：删除刚才创建的立方体。
**指令**："把那个叫 Base_Cube 的立方体删掉。"
**预期结果**：AI 调用 `blender_object_delete`，参数 `name='Base_Cube'`。

---

## 7. 进阶资源

完成本章后，你可以继续学习以下内容：
- [02_几何体创建与变换](./02_几何体创建与变换.md)：学习如何移动、旋转和缩放物体。
- [03_材质与着色器入门](./03_材质与着色器入门.md)：为你的模型穿上漂亮的衣服。

---

## 8. 快速参考卡片

| 任务 | 推荐指令示例 | 对应 MCP 工具 |
| :--- | :--- | :--- |
| 查看版本 | "查看 Blender 信息" | `blender_get_info` |
| 列出场景 | "有哪些场景？" | `blender_scene_list` |
| 创建立方体 | "新建一个立方体" | `blender_object_create` |
| 删除物体 | "删除名为 Cube 的物体" | `blender_object_delete` |

---
*祝你在 Blender 的 3D 世界中玩得开心！*
