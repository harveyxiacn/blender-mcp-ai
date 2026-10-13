> This document is also available at the repository root: [SECURITY.md](../../SECURITY.md)

# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

We actively maintain and apply security fixes to the latest 0.1.x release.

## Reporting a Vulnerability

If you discover a security vulnerability in Blender MCP, please report it responsibly.

**Preferred methods:**

1. **GitHub Security Advisories** - Open a private advisory at [https://github.com/harveyxiacn/blender-mcp-ai/security/advisories/new](https://github.com/harveyxiacn/blender-mcp-ai/security/advisories/new).
2. **Email** - Contact the project maintainers directly with "SECURITY" in the subject line.

**Do not** open a public GitHub issue for security vulnerabilities.

### Response Timeline

- **Acknowledgement**: within 48 hours
- **Initial assessment**: within 7 days
- **Fix or mitigation**: target within 30 days for critical issues

## Security Considerations

See the [root SECURITY.md](../../SECURITY.md) for full details on:

1. **Arbitrary Code Execution** via `execute_python` - mitigated by localhost binding, code size limits, and timeout
2. **TCP Socket Communication** - bound to `127.0.0.1` by default
3. **File Path Operations** - validate paths and restrict to known directories
4. **Dependency Supply Chain** - pin dependencies and monitor for vulnerabilities
