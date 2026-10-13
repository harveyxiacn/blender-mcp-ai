# 更新日志

Blender MCP 的所有重要变更记录。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [0.4.0] - 2026-10-13

### 变更

- **项目更名为 `blender-mcp-ai`** —— 仓库迁至
  `github.com/harveyxiacn/blender-mcp-ai`（旧链接自动重定向），分发包名与命令行
  均为 `blender-mcp-ai`。旧名与另一个项目撞名，而 PyPI 上的 `blender-mcp`
  属于那个项目——`pip install blender-mcp` 从来装的都不是本软件。
  **如果你的 MCP 客户端配置里写的还是 `blender-mcp`，请改成 `blender-mcp-ai`。**
  本项目暂无 PyPI 发布，请从源码安装。
- **角色比例重写** —— `blender_character_template_create` 现在由**同一套骨架**推导
  头、颈、躯干、胯、腿，各部件真正接得上。此前头部悬浮在躯干上方 0.22 m、
  眼睛穿透脸部、手臂埋在胸腔里。生成的角色外观会与 0.3.1 不同。
- 版权归属改为真实作者，不再是虚构的 "Blender MCP Contributors"；
  `bl_info` 也上报真实版本号，而非 `(0, 1, 0)`。

### 新增

- **`scripts/demo_tour.py`** —— 通过 MCP socket 搭出分八层的演示场景，每层一个集合，
  跑完直接打印每层怎么看。新人确认安装是否可用最快的方式。
- **`docs/en/TOUR.md`** / **`docs/zh/TOUR.md`** —— 配套的逐层图文教程。
- **Unity / Quest 游戏引擎 FBX 导出** —— `blender_export_fbx` 现在暴露完整的
  轴向/变换控制，并提供面向非骨骼道具与场景的 `unity_static_preset` 预设
  （`axis_forward=-Z`、`axis_up=Y`、`use_space_transform`、`bake_space_transform`
  使模型以零变换导入、无残留 -90° X 旋转，`mesh_smooth_type=FACE`，仅 Mesh/Empty）。
  新增参数：`axis_forward`、`axis_up`、`use_space_transform`、`bake_space_transform`、
  `apply_unit_scale`、`mesh_smooth_type`、`object_types`、`path_mode`。
  除非显式设置预设或参数，默认值保持向后兼容。
- **零变换导出保护** —— 在 `bake_space_transform` 下自动把导出物体的 `.location`
  归零（导出后还原），让道具在 Unity 中落在 (0,0,0)，并对未应用的旋转/缩放给出警告。
  由 `zero_transform_for_export`（默认 True）控制，导出结果会报告
  `zeroed_for_export` 与 `warnings`。
- **`blender_verify_fbx`** —— 重新导入导出的 FBX 并断言引擎就绪：世界原点 (0,0,0)、
  三角面预算、单文件单物体、材质/自发光报告。返回 PASS/FAIL，便于建模智能体自检。
- **`blender_get_object_info(include_transform_check=True)`** —— 新增 `unity_ready`
  区块（世界坐标、位置/旋转/缩放是否为单位值、`will_import_at_origin`、提示），
  能暴露 `mesh_stats` 看不出来的烘焙位移陷阱。
- **docs/UNITY_QUEST_EXPORT.md** —— 移动 VR（Quest）导出检查清单：面数预算、
  原点/轴向规则、静态预设、三角面数校验。

### 修复

- **多字节 UTF-8 载荷不再断连（issue #2）** —— addon 原本对每个 `recv()` 分块立即
  decode，多字节字符被切开时会抛 `UnicodeDecodeError`，那条消息**根本没执行**就被丢弃。
  现在按字节缓冲、只在完整行边界 decode。同一函数里另修两处：`send()` 可能只写一部分
  导致换行分帧错位（改为 `sendall()`）；协议错误现在返回 `PROTOCOL_ERROR` 响应，
  而不是静默断连。
- **长时间操作不再掐断正常连接** —— 渲染/导出会占住 Blender 主线程，addon 在此期间
  无法应答 `system.get_info`。客户端却照常心跳、5 秒超时后重连，把好好的连接断掉。
  现在有命令在途时跳过心跳。实测：25 秒的命令 0 次重连；去掉该保护则报
  "Connection closed"。
- **handler 不再泄漏编辑模式 —— 这是静默数据丢失。** 7 个 handler 进入编辑模式后不退出，
  会话一直停在 `EDIT_MESH`，此后每次 `object.create` 都会替换掉正在编辑的物体：
  编辑模式下连建 3 个只剩 1 个、且被编辑的那个被销毁；对象模式下 3 个都在。
  已修复 `modeling` 的 `select` / `extrude` / `subdivide` / `bevel` 与
  `mesh_edit_advanced` 的 `edit` / `edge_mark` / `select_by_trait`，
  复用了本就存在却从未被调用的 `ensure_object_mode()`。
- **缺参数返回干净的领域错误，而不是在 bpy 内部抛异常** —— handler 用
  `params.get("object_name")` 取值后直接传给 `bpy.data.objects.get(...)`，
  参数缺失或拼错时得到 `None`，`bpy.data.objects.get(None)` 会在 bpy 内部抛异常，
  调用方看到的是 "SystemError: ... returned a result with an exception set"，
  而不是 `OBJECT_NOT_FOUND`。已为 38 个模块中的 240 处补上默认值。
- **错误信封格式不合规不再导致调用崩溃** —— `training.py` 有六处返回
  `"error": "<字符串>"`，但所有消费方都期望 `{code, message}` 结构，
  于是未知 action 会崩成 "'str' object has no attribute 'get'"。
  `enrich_error()` 现在会把非字典的 error 规范化，而不是直接倒下。
- **修改器不再以原始枚举值命名** —— 不给名字添加倒角时，修改器会被命名为 `BEVEL`，
  这也导致 `modifier_apply` 按名字找不到它。灯光与蜡笔模块有同样的写法。
- 订正了文档与 GitHub 描述中过期的工具数量（380 个工具 / 56 个模块，以及各 Profile 数量）。

### 移除

- **`examples/刀剑神域/`** —— 第三方版权角色素材不应存在于 MIT 许可的仓库中。
  以它为 fixture 的 6 个测试现在会在目录缺失时跳过。
- **Discord 社区入口** —— 邀请链接已失效（`discord.gg/rurjWE45` 现在返回
  "Unknown Invite"），因此移除徽章与链接，而不是留着一个点了打不开的死链接。
  社区交流统一到 GitHub Discussions，发布时的自动公告也已停用。

## [0.3.0] - 2026-05-31

### 新增

- **Smart Tools v2 — 视觉反馈与工作流安全**
  - `blender_snapshot_viewport` — 将 3D 视口捕获为 PNG，用于多模态 AI 审查循环
  - `blender_snapshot_render_preview` — 快速低采样渲染预览（保持宽高比）
  - `blender_describe_scene` — 结构化场景摘要（对象数量、材质、相机、渲染设置）
  - `blender_describe_hierarchy` — 完整的父子对象层级树（Markdown 或 JSON）
  - `blender_describe_object` — 深度对象检查（拓扑统计、修改器堆栈、约束、包围盒）
  - `blender_checkpoint_save` — 高风险操作前的命名存档点
  - `blender_checkpoint_restore` — 从命名存档点还原场景
  - `blender_checkpoint_list` — 列出所有存档点及时间戳和对象数量
  - `blender_checkpoint_delete` — 删除存档点以释放磁盘空间
  - `blender_quick_product_shot` — 一键产品可视化（三点布光 + 相机 + 背景板）
  - `blender_quick_turntable` — 一键 360° 旋转动画
  - `blender_quick_scene_setup` — 一键场景设置（工作室/户外/戏剧/极简）

- **错误建议系统**
  - 新增 `enrich_error()` — 为所有错误响应附加可操作的修复建议
  - 所有执行器错误路径均通过 `enrich_error()` 处理

- **项目 Logo 与品牌形象**
  - 新增官方 Blender MCP Logo（`docs/assets/logo.jpg`）
  - Logo 已嵌入 README 头部

- **全面的实时集成测试套件**
  - `tests/run_live_test.py`: 121个测试覆盖所有50+处理器类别，针对实时Blender实例
  - `tests/create_style_scenes.py`: 264条命令演示，创建3个完整场景（3A游戏、动漫、像素风格）
  - `tests/test_new_tools.py`: Smart Tools v2 模块导入、处理器动作和配置集成的单元测试

- **社区基础设施**
  - 启用 GitHub Discussions
  - 添加 GitHub Topics 提升可发现性
  - 新增 FUNDING.yml（GitHub 赞助按钮）
  - 新增 CODEOWNERS（PR 自动分配审核人）

### 变更

- **版本升级**：0.1.0 → 0.3.0，开发状态 Alpha → Beta
- **Blender 5.x 兼容性修复（50+ 处理器文件）**
  - 修复 EEVEE 引擎名称：增加版本感知兼容层（`handlers/compat.py`）
  - 修复 `bpy.data.objects.get(None)` 在 Blender 5.x 中的崩溃问题
  - 修复动画处理器中 `Action.fcurves` 的删除问题（5.x 分层动作系统）
  - 修复物理处理器中 `ClothSettings.collision_settings` 的位置变更
  - Black 格式化 151 个文件保持一致性
- **tools/__init__.py**：补充 `snapshot`、`describe`、`checkpoint`、`quick` 的缺失导出

### 修复

- **CI 流水线全绿**
  - 修复 6696 个 ruff lint 错误，141 个 black 格式问题，414 个 mypy 类型错误
  - 从 pytest 收集中排除实时测试文件（需要运行中的 Blender）
  - 移除已弃用的 ruff 规则（ANN101、ANN102）

### 变更

- **Blender 5.x 兼容性修复（50+处理器文件）**
  - 修复EEVEE引擎名称：`BLENDER_EEVEE_NEXT` → `BLENDER_EEVEE`，增加版本感知兼容层（`handlers/compat.py`）
  - 修复`bpy.data.objects.get(None)`崩溃问题（Blender 5.x抛出异常而非返回None）
  - 修复`Action.fcurves`移除问题（5.x使用分层动作系统）
  - 修复`ClothSettings.collision_settings`属性位置变更
  - 修复`bpy_prop_collection.__contains__`类型检查
  - 曲线创建添加默认控制点
  - 偏好设置处理器增加None键处理
  - Black格式化151个文件

### 修复

- **CI流水线全绿**
  - 修复6696个ruff lint错误（自动修复 + addon/examples/tests按文件忽略规则）
  - 修复141个black格式化问题
  - 修复414个mypy类型错误（放宽addon代码配置，TYPE_CHECKING导入）
  - 从pytest收集中排除实时测试文件（需要运行Blender实例）
  - 移除已弃用的ruff规则（ANN101, ANN102）

## [Unreleased] - 2026-03-04

### 新增

- **自动化生产线工具（Pipeline）**
  - 新增 `blender_pipeline_generate_character`：角色模板 + 发型/服装/配饰 + 自动绑定 + 风格应用
  - 新增 `blender_pipeline_generate_prop`：道具创建 + 风格 + 程序化材质 + 自动 UV
  - 新增 `blender_pipeline_assemble_scene`：环境/地面/灯光/相机/渲染参数一键组装

- **质量审计工具（Quality Audit）**
  - 新增 `blender_quality_audit_topology`：拓扑审计（N-gon、非流形、松散点）
  - 新增 `blender_quality_audit_uv`：UV 审计（利用率、拉伸、重叠）
  - 新增 `blender_quality_audit_performance`：性能预算审计（三角面、估算 draw call）
  - 新增 `blender_quality_audit_full`：拓扑 + UV + 性能综合评分与等级输出

- **自动化 Skill 组**
  - 新增 `automation` Skill，组合 `pipeline`、`quality_audit`、`style_presets`、`procedural_materials`
  - 支持从“自动生成”到“自动验收”的闭环工作流

- **拓扑节点辅助工具**
  - 新增 `addon/blender_mcp_addon/handlers/node_utils.py`
  - 提供共享的 `find_principled_bsdf()`，用于材质节点安全查找

- **测试覆盖扩展**
  - 新增连接、配置、工具配置、Skill 管理器、Server 兼容别名、工具导出、Principled BSDF 回归等测试
  - 测试总数从 27 项扩展到 34 项

- **连接状态工具**
  - 新增 `blender_connection_status`，可查询 MCP 与 Blender 的连接状态、重连次数、失败命令数、待处理请求等诊断信息

- **统一配置模块**
  - 新增 `src/blender_mcp/config.py`
  - 支持通过环境变量配置主机、端口、超时、重连与日志级别等运行参数

### 变更

- **SkillManager 兼容性升级**
  - 适配新版 FastMCP 工具管理方式，修复动态激活/停用 Skill 时的工具快照与卸载逻辑

- **工具配置扩展**
  - `tools_config.py` 新增 `AUTOMATION_MODULES`
  - `focused`、`standard`、`full` Profile 现已纳入 `pipeline` 和 `quality_audit`

- **工具导出与注册完善**
  - `pipeline` 与 `quality_audit` 接入模块注册表与 `tools.__all__` 导出

- **Blender 5.0.1 集成验证**
  - 回归测试通过：`test_comprehensive.py` 133/133、`test_all_tools.py` 23/23
  - 自动化流程实测通过：角色/道具/场景流水线 + 全量质量审计

- **连接层稳定性增强**
  - `BlenderConnection` 增加自动重连与心跳机制
  - 命令发送失败时支持重连后重试
  - 扩大读取缓冲区并增强 UTF-8 解码容错
  - 新增连接统计信息（总命令数、失败数、重连次数等）

- **Addon 主线程等待机制优化**
  - 使用 `threading.Event.wait()` 替代 `sleep` 轮询等待，降低 CPU 空转

- **CLI 默认配置来源统一**
  - `__main__.py` 与 `server.py` 默认参数改为从统一配置模块读取

### 修复

- **Principled BSDF 递归缺陷**
  - 修复 `ai_generation`、`character_template`、`substance`、`vr_ar`、`zbrush` 中的递归调用错误
  - 统一改为使用共享 helper，避免运行时崩溃风险

- **Server 向后兼容**
  - 为 `BlenderMCPServer` 增加 `send_command()` 别名，兼容仍在调用旧接口的工具模块

- **Pipeline 工具注册与参数兼容**
  - 修复 `pipeline/quality_audit` 在 FastMCP 下的注册错误
  - 改进相机激活参数兼容（同时传递 `camera_name` 与 `name`）

- **Addon 启动参数问题**
  - 修复 `start_server()` 未正确传递 `host` 参数的问题

- **Python 执行安全性**
  - 为 `execute_python` 增加空代码校验、代码大小限制与危险模式拦截

## [0.2.0] - 2026-02-11

### 新增

- **Skill 系统（动态工具加载）**
  - `SkillManager` 按需激活/停用工具组
  - 3 个元工具：`blender_list_skills`、`blender_activate_skill`、`blender_deactivate_skill`
  - 11 个 Skill 组覆盖全部 200+ 工具
  - `tools/list_changed` MCP 通知，客户端自动刷新
  - 激活时返回工作流指引
  - 新增 `"skill"` 工具 Profile（推荐，~31 个启动工具）

- **高级网格编辑**（5 个工具）
  - `blender_mesh_edit_advanced` — 内嵌、桥接、旋转、切刀、填充、对称化等
  - `blender_mesh_edge_mark` — 折痕、锐边、缝合、倒角权重
  - `blender_mesh_select_by_trait` — 非流形、松散、边界等
  - `blender_vertex_group` — 顶点组管理
  - `blender_vertex_color` — 顶点颜色绘制

- **风格预设**（3 个工具）
  - `blender_style_setup` — 一键风格配置（像素风→3A，8 种预设）
  - `blender_outline_effect` — 描边（Solidify/Freestyle/Grease Pencil）
  - `blender_bake_maps` — 高低模烘焙工作流

- **程序化材质**（2 个工具）
  - `blender_procedural_material` — 8 大类 67 种预设
  - `blender_material_wear` — 磨损效果（边缘磨损、划痕、锈蚀、灰尘等）

- **增强对象创建**
  - `mesh_params` 支持参数化网格创建（段数、半径、深度等）
  - 所有网格基本体的完整参数控制

- **扩展修改器支持**
  - 45 种修改器类型（从 12 种扩展）
  - 新增：螺旋、线框、焊接、重建网格、构建、多级精度、铸型、曲线、晶格等

### 变更

- 默认 `TOOL_PROFILE` 从 `"focused"` 改为 `"skill"`
- 启动工具数从 ~100 减少到 ~31（减少 69%）

## [0.1.0] - 2026-01-15

### 新增

- 首次发布
- 基于 FastMCP 框架的 MCP 服务器
- Blender 插件（TCP 服务器）
- 核心工具模块：场景、对象、建模、材质、灯光、相机、动画、渲染、实用工具、导出
- 扩展模块：角色模板、骨骼绑定、自动绑定、物理、约束、节点、合成器、雕刻、纹理绘制、批处理、资产、动画预设、世界环境、版本控制、AI 生成、VR/AR、Substance、ZBrush、云渲染、协作、培训
- 多 IDE 支持：Cursor、Windsurf、Claude Desktop
- 插件热更新开发功能
- 工具 Profile：minimal、focused、standard、full
