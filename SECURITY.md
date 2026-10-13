# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

We actively maintain and apply security fixes to the latest 0.1.x release.

## Reporting a Vulnerability

If you discover a security vulnerability in Blender MCP, please report it responsibly.

**Preferred methods:**

1. **GitHub Security Advisories** — Open a private advisory at [https://github.com/harveyxiacn/blender-mcp-ai/security/advisories/new](https://github.com/harveyxiacn/blender-mcp-ai/security/advisories/new). This keeps the report confidential until a fix is available.
2. **Email** — Contact the project maintainers directly. Please include "SECURITY" in the subject line so the report is prioritized.

**Do not** open a public GitHub issue for security vulnerabilities. Public disclosure before a fix is available puts all users at risk.

### What to Include

- A clear description of the vulnerability
- Steps to reproduce or a proof of concept
- Affected versions
- Potential impact

### Response Timeline

- **Acknowledgement**: within 48 hours of receipt
- **Initial assessment**: within 7 days
- **Fix or mitigation**: target within 30 days for critical issues

We will coordinate disclosure timing with the reporter and credit them (unless they prefer anonymity).

## Security Considerations

Blender MCP bridges AI assistants and Blender through a TCP socket and exposes powerful automation tools. Operators and developers should be aware of the following risks and the mitigations in place.

### 1. Arbitrary Code Execution via `execute_python`

The `blender_execute_python` tool allows callers to run arbitrary Python code inside the Blender process. This is by design — it is the primary mechanism for advanced automation — but it means that any entity with access to the MCP server can execute code with the full privileges of the Blender process.

**Built-in mitigations:**

- The MCP server communicates with the Blender addon over a TCP socket bound to `127.0.0.1` by default, so remote hosts cannot connect without explicit reconfiguration.
- A configurable maximum code size (`BLENDER_MCP_MAX_CODE_SIZE`, default 100 000 characters) limits payload size.
- A per-execution timeout (default 30 s, max 300 s) prevents runaway scripts.

**Recommendations:**

- Never expose the MCP server or the Blender addon socket to untrusted networks.
- If you change the bind address from `127.0.0.1`, ensure appropriate firewall rules are in place.
- Review any code an AI assistant proposes before allowing execution in production environments.

### 2. TCP Socket Communication

The server and the Blender addon communicate over a plain TCP socket (default `127.0.0.1:9876`).

**Built-in mitigations:**

- Binding to `127.0.0.1` restricts connections to the local machine.
- A heartbeat mechanism detects stale or dropped connections.

**Recommendations:**

- Do not bind to `0.0.0.0` or a public interface unless you have network-level access controls.
- Consider a reverse proxy with authentication if remote access is required.

### 3. File Path Operations

Several tools (export, import, render) read from or write to the filesystem using paths provided by the caller.

**Recommendations:**

- Validate and restrict file paths to a known working directory when possible.
- Be cautious with paths that include `..` segments or absolute paths outside expected directories.
- Run Blender under a user account with the minimum filesystem permissions required.

### 4. Dependency Supply Chain

Blender MCP depends on third-party Python packages listed in `pyproject.toml`.

**Recommendations:**

- Pin dependencies and review updates before upgrading.
- Use `uv.lock` to ensure reproducible installs.
- Monitor dependencies for known vulnerabilities with tools such as `pip-audit` or GitHub Dependabot.

## Scope

This policy covers the Blender MCP server (`src/blender_mcp`), the Blender addon (`addon/`), and the official build and test tooling. It does not cover Blender itself or third-party MCP clients.

## License

Blender MCP is released under the [MIT License](LICENSE). This security policy does not alter the terms of that license.
