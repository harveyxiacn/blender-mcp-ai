# Blender MCP API 参考文档

## 概述

本文档详细描述了 Blender MCP 提供的所有工具（Tools）及其参数。所有工具都通过 MCP 协议暴露，可在支持 MCP 的 IDE 中使用。

状态说明（2026-03-10）：仓库当前已包含 56 个工具模块、380 个工具注册项。本文档目前对稳定/核心工具族最完整；`training`、`sport_character`、`style_presets`、`procedural_materials` 以及实验性的 automation 相关模块，仍建议结合源码与项目审查报告一并查看。

## 工具命名规范

所有工具名称遵循以下格式：
```
blender_{category}_{action}
```

例如：
- `blender_object_create` - 创建对象
- `blender_material_assign` - 分配材质
- `blender_animation_keyframe_insert` - 插入关键帧

---

## 1. 场景管理 (Scene)

### blender_scene_create

创建新场景。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `name` | string | 是 | - | 场景名称 |
| `copy_from` | string | 否 | null | 复制来源场景名称 |

**返回**：
```json
{
  "scene_name": "MyScene",
  "message": "Successfully created scene 'MyScene'"
}
```

**示例**：
```
创建一个名为 "MainScene" 的新场景
```

---

### blender_scene_list

列出所有场景。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `response_format` | string | 否 | "markdown" | 输出格式：markdown 或 json |

**返回**：
```json
{
  "scenes": [
    {"name": "Scene", "objects_count": 3, "is_active": true},
    {"name": "MyScene", "objects_count": 0, "is_active": false}
  ],
  "total": 2
}
```

---

### blender_scene_get_info

获取场景详细信息。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `scene_name` | string | 否 | null | 场景名称，为空则返回当前场景 |

**返回**：
```json
{
  "name": "Scene",
  "frame_start": 1,
  "frame_end": 250,
  "frame_current": 1,
  "fps": 24,
  "objects_count": 3,
  "unit_system": "METRIC",
  "unit_scale": 1.0
}
```

---

### blender_scene_set_settings

设置场景参数。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `scene_name` | string | 否 | null | 场景名称 |
| `frame_start` | int | 否 | null | 起始帧 |
| `frame_end` | int | 否 | null | 结束帧 |
| `fps` | int | 否 | null | 帧率 (1-120) |
| `unit_system` | string | 否 | null | 单位系统：NONE, METRIC, IMPERIAL |
| `unit_scale` | float | 否 | null | 单位缩放 |

---

## 2. 对象操作 (Object)

### blender_object_create

创建新对象。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `type` | string | 是 | - | 对象类型 |
| `name` | string | 否 | 自动生成 | 对象名称 |
| `location` | [float, float, float] | 否 | [0, 0, 0] | 位置坐标 |
| `rotation` | [float, float, float] | 否 | [0, 0, 0] | 旋转角度（弧度） |
| `scale` | [float, float, float] | 否 | [1, 1, 1] | 缩放 |

**支持的对象类型**：
- 网格：`CUBE`, `SPHERE`, `CYLINDER`, `CONE`, `TORUS`, `PLANE`, `CIRCLE`, `GRID`, `MONKEY`, `ICO_SPHERE`, `UV_SPHERE`
- 曲线：`BEZIER`, `NURBS_CURVE`, `NURBS_CIRCLE`, `PATH`
- 曲面：`NURBS_SURFACE`
- 文本：`TEXT`
- 空物体：`EMPTY`, `EMPTY_SPHERE`, `EMPTY_CUBE`, `EMPTY_ARROWS`
- 其他：`ARMATURE`, `LATTICE`, `CAMERA`, `LIGHT`

**返回**：
```json
{
  "object_name": "Cube",
  "object_type": "MESH",
  "location": [0, 0, 0],
  "message": "Successfully created CUBE object 'Cube'"
}
```

**示例**：
```
在位置 (0, 0, 2) 创建一个球体
```

---

### blender_object_delete

删除对象。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `name` | string | 是 | - | 对象名称 |
| `delete_data` | bool | 否 | true | 是否同时删除对象数据 |

---

### blender_object_duplicate

复制对象。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `name` | string | 是 | - | 源对象名称 |
| `new_name` | string | 否 | 自动生成 | 新对象名称 |
| `linked` | bool | 否 | false | 是否关联复制（共享数据） |
| `offset` | [float, float, float] | 否 | [0, 0, 0] | 位置偏移 |

---

### blender_object_transform

变换对象（位置、旋转、缩放）。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `name` | string | 是 | - | 对象名称 |
| `location` | [float, float, float] | 否 | null | 新位置（绝对值） |
| `rotation` | [float, float, float] | 否 | null | 新旋转（弧度） |
| `scale` | [float, float, float] | 否 | null | 新缩放 |
| `delta_location` | [float, float, float] | 否 | null | 位置增量 |
| `delta_rotation` | [float, float, float] | 否 | null | 旋转增量 |
| `delta_scale` | [float, float, float] | 否 | null | 缩放增量 |

**示例**：
```
将 Cube 移动到位置 (5, 0, 0) 并放大 2 倍
```

---

### blender_object_select

选择对象。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `names` | string[] | 否 | null | 要选择的对象名称列表 |
| `pattern` | string | 否 | null | 选择匹配模式（支持通配符） |
| `deselect_all` | bool | 否 | true | 是否先取消所有选择 |
| `set_active` | string | 否 | null | 设置活动对象 |

---

### blender_object_list

列出场景中的对象。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `type_filter` | string | 否 | null | 过滤对象类型 |
| `name_pattern` | string | 否 | null | 名称匹配模式 |
| `limit` | int | 否 | 50 | 返回数量限制 |
| `response_format` | string | 否 | "markdown" | 输出格式 |

**返回**：
```json
{
  "objects": [
    {
      "name": "Cube",
      "type": "MESH",
      "location": [0, 0, 0],
      "visible": true
    }
  ],
  "total": 1
}
```

---

### blender_object_get_info

获取对象详细信息。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `name` | string | 是 | - | 对象名称 |
| `include_mesh_stats` | bool | 否 | true | 包含网格统计 |
| `include_modifiers` | bool | 否 | true | 包含修改器信息 |
| `include_materials` | bool | 否 | true | 包含材质信息 |

**返回**：
```json
{
  "name": "Cube",
  "type": "MESH",
  "location": [0, 0, 0],
  "rotation_euler": [0, 0, 0],
  "scale": [1, 1, 1],
  "dimensions": [2, 2, 2],
  "mesh_stats": {
    "vertices": 8,
    "edges": 12,
    "faces": 6,
    "triangles": 12
  },
  "modifiers": [],
  "materials": ["Material"]
}
```

---

## 3. 建模 (Modeling)

### blender_mesh_edit_mode

进入或退出编辑模式。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `object_name` | string | 是 | - | 对象名称 |
| `enter` | bool | 否 | true | true=进入，false=退出 |

---

### blender_mesh_select

在编辑模式下选择网格元素。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `object_name` | string | 是 | - | 对象名称 |
| `select_mode` | string | 否 | "VERT" | 选择模式：VERT, EDGE, FACE |
| `action` | string | 是 | - | 操作：ALL, NONE, INVERT, RANDOM, LINKED |
| `random_ratio` | float | 否 | 0.5 | 随机选择比例 (0-1) |

---

### blender_mesh_extrude

挤出操作。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `object_name` | string | 是 | - | 对象名称 |
| `direction` | [float, float, float] | 否 | [0, 0, 1] | 挤出方向向量 |
| `distance` | float | 否 | 1.0 | 挤出距离 |
| `use_normal` | bool | 否 | true | 沿法线方向 |

---

### blender_mesh_subdivide

细分网格。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `object_name` | string | 是 | - | 对象名称 |
| `cuts` | int | 否 | 1 | 切割次数 (1-100) |
| `smoothness` | float | 否 | 0.0 | 平滑度 (0-1) |

---

### blender_mesh_bevel

倒角操作。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `object_name` | string | 是 | - | 对象名称 |
| `width` | float | 否 | 0.1 | 倒角宽度 |
| `segments` | int | 否 | 1 | 分段数 (1-100) |
| `profile` | float | 否 | 0.5 | 轮廓形状 (0-1) |
| `affect` | string | 否 | "EDGES" | 影响：VERTICES, EDGES |

---

### blender_modifier_add

添加修改器。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `object_name` | string | 是 | - | 对象名称 |
| `modifier_type` | string | 是 | - | 修改器类型 |
| `modifier_name` | string | 否 | 自动生成 | 修改器名称 |
| `settings` | object | 否 | {} | 修改器设置 |

**常用修改器类型**：
- `SUBSURF` - 表面细分
- `MIRROR` - 镜像
- `ARRAY` - 阵列
- `BEVEL` - 倒角
- `SOLIDIFY` - 实体化
- `BOOLEAN` - 布尔
- `ARMATURE` - 骨架
- `SKIN` - 蒙皮
- `DECIMATE` - 精简

**修改器设置示例**：
```json
{
  "modifier_type": "SUBSURF",
  "settings": {
    "levels": 2,
    "render_levels": 3,
    "use_limit_surface": true
  }
}
```

---

### blender_modifier_apply

应用修改器。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `object_name` | string | 是 | - | 对象名称 |
| `modifier_name` | string | 是 | - | 修改器名称 |

---

### blender_boolean_operation

布尔运算。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `object_name` | string | 是 | - | 主对象名称 |
| `target_name` | string | 是 | - | 目标对象名称 |
| `operation` | string | 是 | - | 运算类型：UNION, DIFFERENCE, INTERSECT |
| `apply` | bool | 否 | true | 是否立即应用 |
| `hide_target` | bool | 否 | true | 隐藏目标对象 |

---

## 4. 材质 (Material)

### blender_material_create

创建新材质。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `name` | string | 是 | - | 材质名称 |
| `color` | [float, float, float, float] | 否 | [0.8, 0.8, 0.8, 1.0] | RGBA 颜色 |
| `metallic` | float | 否 | 0.0 | 金属度 (0-1) |
| `roughness` | float | 否 | 0.5 | 粗糙度 (0-1) |
| `use_nodes` | bool | 否 | true | 使用节点材质 |

**示例**：
```
创建一个红色金属材质
```

---

### blender_material_assign

将材质分配给对象。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `object_name` | string | 是 | - | 对象名称 |
| `material_name` | string | 是 | - | 材质名称 |
| `slot_index` | int | 否 | 0 | 材质槽索引 |

---

### blender_material_set_properties

设置材质属性。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `material_name` | string | 是 | - | 材质名称 |
| `color` | [float, float, float, float] | 否 | null | RGBA 颜色 |
| `metallic` | float | 否 | null | 金属度 |
| `roughness` | float | 否 | null | 粗糙度 |
| `specular` | float | 否 | null | 高光强度 |
| `emission_color` | [float, float, float, float] | 否 | null | 自发光颜色 |
| `emission_strength` | float | 否 | null | 自发光强度 |
| `alpha` | float | 否 | null | 透明度 |
| `blend_mode` | string | 否 | null | 混合模式：OPAQUE, CLIP, HASHED, BLEND |

---

### blender_material_add_texture

为材质添加纹理。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `material_name` | string | 是 | - | 材质名称 |
| `texture_path` | string | 是 | - | 纹理文件路径 |
| `texture_type` | string | 否 | "COLOR" | 纹理类型：COLOR, NORMAL, ROUGHNESS, METALLIC, EMISSION |
| `mapping` | string | 否 | "UV" | 映射方式：UV, BOX, SPHERE, CYLINDER |

---

## 5. 灯光 (Lighting)

### blender_light_create

创建灯光。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `type` | string | 是 | - | 灯光类型：POINT, SUN, SPOT, AREA |
| `name` | string | 否 | 自动生成 | 灯光名称 |
| `location` | [float, float, float] | 否 | [0, 0, 5] | 位置 |
| `rotation` | [float, float, float] | 否 | [0, 0, 0] | 旋转 |
| `color` | [float, float, float] | 否 | [1, 1, 1] | RGB 颜色 |
| `energy` | float | 否 | 1000.0 | 能量/强度（瓦特） |
| `radius` | float | 否 | 0.25 | 灯光半径 |

**灯光类型说明**：
- `POINT` - 点光源，向所有方向发光
- `SUN` - 太阳光，平行光源
- `SPOT` - 聚光灯，锥形光源
- `AREA` - 面光源，模拟柔和光

---

### blender_light_set_properties

设置灯光属性。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `light_name` | string | 是 | - | 灯光名称 |
| `color` | [float, float, float] | 否 | null | RGB 颜色 |
| `energy` | float | 否 | null | 能量 |
| `radius` | float | 否 | null | 半径 |
| `spot_size` | float | 否 | null | 聚光灯角度（弧度） |
| `spot_blend` | float | 否 | null | 聚光灯边缘柔和度 |
| `shadow_soft_size` | float | 否 | null | 阴影柔和度 |
| `use_shadow` | bool | 否 | null | 是否投射阴影 |

---

### blender_hdri_setup

设置 HDRI 环境光。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `hdri_path` | string | 是 | - | HDRI 文件路径 |
| `strength` | float | 否 | 1.0 | 环境光强度 |
| `rotation` | float | 否 | 0.0 | 旋转角度（弧度） |

---

## 6. 相机 (Camera)

### blender_camera_create

创建相机。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `name` | string | 否 | "Camera" | 相机名称 |
| `location` | [float, float, float] | 否 | [0, -10, 5] | 位置 |
| `rotation` | [float, float, float] | 否 | [1.1, 0, 0] | 旋转 |
| `lens` | float | 否 | 50.0 | 焦距 (mm) |
| `sensor_width` | float | 否 | 36.0 | 传感器宽度 (mm) |
| `set_active` | bool | 否 | true | 设为活动相机 |

---

### blender_camera_set_properties

设置相机属性。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `camera_name` | string | 是 | - | 相机名称 |
| `lens` | float | 否 | null | 焦距 |
| `sensor_width` | float | 否 | null | 传感器宽度 |
| `clip_start` | float | 否 | null | 近裁剪 |
| `clip_end` | float | 否 | null | 远裁剪 |
| `dof_focus_object` | string | 否 | null | 景深焦点对象 |
| `dof_focus_distance` | float | 否 | null | 景深焦点距离 |
| `dof_aperture_fstop` | float | 否 | null | 光圈值 |

---

### blender_camera_look_at

使相机朝向目标。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `camera_name` | string | 是 | - | 相机名称 |
| `target` | string 或 [float, float, float] | 是 | - | 目标对象名称或位置坐标 |
| `use_constraint` | bool | 否 | false | 使用约束（持续朝向） |

---

## 7. 动画 (Animation)

### blender_keyframe_insert

插入关键帧。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `object_name` | string | 是 | - | 对象名称 |
| `data_path` | string | 是 | - | 数据路径 |
| `frame` | int | 否 | 当前帧 | 帧编号 |
| `value` | any | 否 | null | 属性值 |

**常用数据路径**：
- `location` - 位置
- `rotation_euler` - 欧拉旋转
- `rotation_quaternion` - 四元数旋转
- `scale` - 缩放
- `location[0]` - X 位置
- `rotation_euler[2]` - Z 旋转

**示例**：
```
为 Cube 在第 1 帧和第 60 帧插入位置关键帧，创建移动动画
```

---

### blender_keyframe_delete

删除关键帧。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `object_name` | string | 是 | - | 对象名称 |
| `data_path` | string | 是 | - | 数据路径 |
| `frame` | int | 否 | 当前帧 | 帧编号 |

---

### blender_animation_set_interpolation

设置关键帧插值类型。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `object_name` | string | 是 | - | 对象名称 |
| `interpolation` | string | 是 | - | 插值类型 |

**插值类型**：
- `CONSTANT` - 常量（无过渡）
- `LINEAR` - 线性
- `BEZIER` - 贝塞尔曲线
- `SINE` - 正弦
- `QUAD` - 二次
- `CUBIC` - 三次
- `QUART` - 四次
- `QUINT` - 五次
- `EXPO` - 指数
- `CIRC` - 圆形
- `BACK` - 回弹
- `BOUNCE` - 弹跳
- `ELASTIC` - 弹性

---

### blender_timeline_set_range

设置时间线范围。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `frame_start` | int | 否 | null | 起始帧 |
| `frame_end` | int | 否 | null | 结束帧 |
| `frame_current` | int | 否 | null | 当前帧 |

---

## 8. 角色系统 (Character)

### blender_character_create_humanoid

创建人形基础网格。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `name` | string | 否 | "Character" | 角色名称 |
| `height` | float | 否 | 1.8 | 身高（米） |
| `body_type` | string | 否 | "AVERAGE" | 体型：SLIM, AVERAGE, MUSCULAR, HEAVY |
| `gender` | string | 否 | "NEUTRAL" | 性别：MALE, FEMALE, NEUTRAL |
| `subdivisions` | int | 否 | 2 | 细分级别 (0-4) |

---

### blender_character_add_face_features

添加面部特征。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `character_name` | string | 是 | - | 角色名称 |
| `eye_size` | float | 否 | 1.0 | 眼睛大小 (0.5-1.5) |
| `nose_length` | float | 否 | 1.0 | 鼻子长度 (0.5-1.5) |
| `mouth_width` | float | 否 | 1.0 | 嘴宽度 (0.5-1.5) |
| `jaw_width` | float | 否 | 1.0 | 下巴宽度 (0.5-1.5) |

---

## 9. 骨骼绑定 (Rigging)

### blender_armature_create

创建骨架。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `name` | string | 否 | "Armature" | 骨架名称 |
| `location` | [float, float, float] | 否 | [0, 0, 0] | 位置 |

---

### blender_bone_add

添加骨骼。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `armature_name` | string | 是 | - | 骨架名称 |
| `bone_name` | string | 是 | - | 骨骼名称 |
| `head` | [float, float, float] | 是 | - | 骨头位置 |
| `tail` | [float, float, float] | 是 | - | 骨尾位置 |
| `parent` | string | 否 | null | 父骨骼名称 |
| `use_connect` | bool | 否 | false | 连接到父骨骼 |

---

### blender_armature_generate_rig

使用 Rigify 生成完整绑定。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `target_mesh` | string | 是 | - | 目标网格名称 |
| `rig_type` | string | 否 | "HUMAN" | 绑定类型：HUMAN, QUADRUPED, BIRD, BASIC |
| `auto_weights` | bool | 否 | true | 自动计算权重 |

---

### blender_ik_setup

设置 IK（反向运动学）约束。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `armature_name` | string | 是 | - | 骨架名称 |
| `bone_name` | string | 是 | - | 骨骼名称 |
| `target` | string | 是 | - | 目标对象或骨骼 |
| `chain_length` | int | 否 | 2 | IK 链长度 |
| `pole_target` | string | 否 | null | 极向量目标 |

---

## 10. 渲染 (Render)

### blender_render_settings

设置渲染参数。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `engine` | string | 否 | null | 渲染引擎：CYCLES, EEVEE, EEVEE_NEXT, WORKBENCH |
| `resolution_x` | int | 否 | null | 水平分辨率 |
| `resolution_y` | int | 否 | null | 垂直分辨率 |
| `resolution_percentage` | int | 否 | null | 分辨率百分比 |
| `samples` | int | 否 | null | 采样数 |
| `use_denoising` | bool | 否 | null | 使用降噪 |
| `file_format` | string | 否 | null | 输出格式：PNG, JPEG, EXR, TIFF |
| `output_path` | string | 否 | null | 输出路径 |

---

### blender_render_image

渲染静态图像。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `output_path` | string | 否 | null | 输出路径 |
| `frame` | int | 否 | 当前帧 | 渲染帧 |
| `camera` | string | 否 | 活动相机 | 相机名称 |
| `write_still` | bool | 否 | true | 保存图像 |

**返回**：
```json
{
  "success": true,
  "output_path": "/path/to/render.png",
  "render_time": 12.5,
  "resolution": [1920, 1080]
}
```

---

### blender_render_animation

渲染动画序列。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `output_path` | string | 是 | - | 输出目录 |
| `frame_start` | int | 否 | 场景起始帧 | 起始帧 |
| `frame_end` | int | 否 | 场景结束帧 | 结束帧 |
| `frame_step` | int | 否 | 1 | 帧步长 |

---

## 11. 实用工具 (Utility)

### blender_execute_python

执行 Python 代码（高级用户）。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `code` | string | 是 | - | Python 代码 |
| `timeout` | int | 否 | 30 | 超时时间（秒） |

**注意**：此功能需要在设置中启用，且应谨慎使用。

---

### blender_get_viewport_screenshot

获取视口截图。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `output_path` | string | 否 | 临时文件 | 输出路径 |
| `width` | int | 否 | 800 | 图像宽度 |
| `height` | int | 否 | 600 | 图像高度 |

---

### blender_file_save

保存 Blender 文件。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `filepath` | string | 否 | 当前文件 | 文件路径 |
| `compress` | bool | 否 | true | 压缩文件 |

---

### blender_file_open

打开 Blender 文件。

**参数**：
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `filepath` | string | 是 | - | 文件路径 |
| `load_ui` | bool | 否 | false | 加载 UI 布局 |

---

## 错误代码

| 代码 | 描述 |
|------|------|
| `INVALID_PARAMS` | 参数无效 |
| `OBJECT_NOT_FOUND` | 对象不存在 |
| `MATERIAL_NOT_FOUND` | 材质不存在 |
| `SCENE_NOT_FOUND` | 场景不存在 |
| `OPERATION_FAILED` | 操作失败 |
| `CONNECTION_ERROR` | 连接错误 |
| `TIMEOUT` | 操作超时 |
| `PERMISSION_DENIED` | 权限不足 |
| `FILE_NOT_FOUND` | 文件不存在 |
| `UNSUPPORTED_VERSION` | 不支持的 Blender 版本 |
