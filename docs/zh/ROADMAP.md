# Blender MCP 路线图

## 状态日期

本路线图基于 2026-03-10 的仓库状态整理。

## 已具备的基础

- 51 个服务端工具模块
- 源码中 380 个工具
- 12 个 Skill 分组的按需加载体系
- 插件热更新能力
- training、sport_character、style_presets、procedural_materials 等扩展模块

## 优先级 1：稳定性与执行层对齐

- 补齐 `pipeline` 与 `quality_audit` 的 Blender 插件 handler
- 增加 MCP 类别与插件 handler 类别的一致性自动测试
- 在 Profile 默认值中区分稳定模块与实验性模块
- 从源码自动生成工具/Profile 盘点文档，替代手工维护的统计数字

## 优先级 2：生产工作流加固

- 为烘焙、渲染、导出引入任务队列
- 为耗时操作增加进度回报与取消机制
- 沉淀角色、道具、场景的可复用资产构建配方
- 增加面向 web、mobile、desktop、hero 质量档位的预设包

## 优先级 3：质量审计到自动修复闭环

- 将质量审计结果转成可执行的修复工作流
- 为 UV 重叠、命名、导出设置、拓扑卫生提供可选自动修复
- 在 GLB/FBX 导出前增加发布前检查

## 优先级 4：资产与协作层

- 为场景/包体提供差异摘要，方便 Review
- 强化资产元数据与检索流程
- 增加 Review、导出、引擎接入的交接包
- 让 cloud_render / collaboration 模块接入真实任务编排
