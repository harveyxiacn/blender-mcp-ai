# Blender MCP 快速开始指南

## 简介

本指南将帮助你在 5 分钟内开始使用 Blender MCP。

## 前置条件

- 已安装 Blender 5.0+ （[下载地址](https://www.blender.org/download/)）
- 已安装 Python 3.10+
- 已安装支持 MCP 的 IDE（如 Cursor）

## 快速安装

### 1. 安装 MCP 服务器

```bash
pip install git+https://github.com/harveyxiacn/blender-mcp-ai.git
```

### 2. 安装 Blender 插件

```bash
python -m blender_mcp install-addon
```

### 3. 配置 IDE

在项目根目录创建 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "blender": {
      "command": "python",
      "args": ["-m", "blender_mcp"]
    }
  }
}
```

### 4. 启动 Blender

打开 Blender，在侧边栏中找到 "MCP" 面板，确认服务状态为 "运行中"。

## 第一个示例

在 IDE 中向 AI 助手发送以下请求：

```
请在 Blender 中创建一个简单的场景：
1. 删除默认的立方体
2. 创建一个球体
3. 给球体添加红色金属材质
4. 添加一个点光源照亮场景
```

AI 将自动调用 Blender MCP 工具完成这些操作。

## 常用命令示例

### 创建对象

```
在 Blender 中创建一个圆柱体，位置在 (2, 0, 0)
```

### 修改材质

```
将 Cube 的材质改为蓝色玻璃效果
```

### 创建动画

```
为 Sphere 创建一个上下跳动的动画，持续 60 帧
```

### 设置渲染

```
设置渲染分辨率为 1920x1080，使用 Cycles 引擎，渲染一张图片到桌面
```

## 下一步

- 阅读 [API 参考](./API_REFERENCE.md) 了解所有可用功能
- 查看 [教程](./TUTORIALS.md) 学习更复杂的项目
- 了解 [架构设计](./ARCHITECTURE.md) 进行自定义开发

## 常见问题

### Q: 无法连接到 Blender？

确保：
1. Blender 正在运行
2. MCP 插件已启用
3. 服务状态显示 "运行中"

### Q: 命令执行失败？

查看：
1. Blender 系统控制台的错误信息
2. IDE 终端的 MCP 服务器日志

### Q: 如何查看执行日志？

```bash
# 启用详细日志
python -m blender_mcp --log-level DEBUG
```
