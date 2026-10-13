# 安全策略

## 支持的版本

| 版本 | 支持状态 |
|------|----------|
| 0.1.x | 支持 |

我们积极维护最新 0.1.x 版本的安全修复。

## 报告漏洞

如果您发现 Blender MCP 中的安全漏洞，请负责任地报告。

**首选方式：**

1. **GitHub 安全公告** — 在 [https://github.com/harveyxiacn/blender-mcp-ai/security/advisories/new](https://github.com/harveyxiacn/blender-mcp-ai/security/advisories/new) 提交私密公告。
2. **邮件** — 直接联系项目维护者，请在主题中注明"SECURITY"。

**请勿**为安全漏洞创建公开的 GitHub Issue。

### 响应时间

- **确认收到**：48 小时内
- **初步评估**：7 天内
- **修复或缓解**：关键问题目标 30 天内

## 安全注意事项

### 1. 通过 `execute_python` 执行任意代码

`blender_execute_python` 工具允许调用方在 Blender 进程内运行任意 Python 代码。这是设计使然——它是高级自动化的主要机制——但这意味着任何能访问 MCP 服务器的实体都可以以 Blender 进程的完整权限执行代码。

**内置缓解措施：**

- MCP 服务器通过默认绑定到 `127.0.0.1` 的 TCP 套接字与 Blender 插件通信，远程主机无法连接。
- 可配置的最大代码大小（`BLENDER_MCP_MAX_CODE_SIZE`，默认 100,000 字符）限制载荷大小。
- 每次执行超时（默认 30 秒，最大 300 秒）防止脚本失控。
- 受限的内置函数集合阻止危险操作（`exec`、`eval`、`__import__` 等）。
- 危险模式检测阻止 `subprocess`、`socket`、`os.system` 等调用。

**建议：**

- 永远不要将 MCP 服务器或 Blender 插件套接字暴露到不受信任的网络。
- 如果将绑定地址从 `127.0.0.1` 更改，请确保有适当的防火墙规则。

### 2. TCP 套接字通信

服务器和 Blender 插件通过纯 TCP 套接字通信（默认 `127.0.0.1:9876`）。

**建议：**

- 不要绑定到 `0.0.0.0` 或公共接口，除非有网络级别的访问控制。
- 如需远程访问，请考虑使用带身份验证的反向代理。

### 3. 文件路径操作

多个工具（导出、导入、渲染）使用调用方提供的路径读写文件系统。

**建议：**

- 尽可能验证并限制文件路径到已知的工作目录。
- 对包含 `..` 段或超出预期目录的绝对路径保持警惕。
- 以最小文件系统权限运行 Blender。

### 4. 依赖供应链

Blender MCP 依赖 `pyproject.toml` 中列出的第三方 Python 包。

**建议：**

- 锁定依赖版本，升级前审查更新。
- 使用 `uv.lock` 确保可复现的安装。
- 使用 `pip-audit` 或 GitHub Dependabot 监控已知漏洞。

## 范围

本策略涵盖 Blender MCP 服务器（`src/blender_mcp`）、Blender 插件（`addon/`）以及官方构建和测试工具。不涵盖 Blender 本身或第三方 MCP 客户端。
