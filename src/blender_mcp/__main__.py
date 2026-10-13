"""
Blender MCP - Command Line Entry Point

Usage:
    python -m blender_mcp [OPTIONS]

Options:
    --host TEXT         Blender connection host [default: 127.0.0.1]
    --port INTEGER      Blender connection port [default: 9876]
    --transport TEXT    Transport mode: stdio, http [default: stdio]
    --http-port INTEGER HTTP server port [default: 8080]
    --log-level TEXT    Log level: DEBUG, INFO, WARNING, ERROR [default: INFO]
    --version           Show version info
    --help              Show help info
"""

import asyncio
import atexit
import contextlib
import logging
import os
import signal
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.logging import RichHandler

from blender_mcp import __version__, config
from blender_mcp.server import BlenderMCPServer

# Use stderr to avoid interfering with MCP stdio communication
console = Console(file=sys.stderr)

# PID file path
_PID_FILE = Path(__file__).parent.parent.parent / ".blender_mcp.pid"


def _get_pid_file() -> Path:
    """Get PID file path (prefer temp directory)"""
    import tempfile

    return Path(tempfile.gettempdir()) / "blender_mcp.pid"


def _cleanup_zombie_processes() -> int:
    """Clean up leftover blender-mcp-ai zombie processes

    Returns:
        Number of processes cleaned up
    """
    current_pid = os.getpid()
    killed = 0

    # Method 1: Clean up via PID file
    pid_file = _get_pid_file()
    if pid_file.exists():
        try:
            old_pid = int(pid_file.read_text().strip())
            if old_pid != current_pid and _is_blender_mcp_process(old_pid):
                os.kill(old_pid, signal.SIGTERM)
                killed += 1
                console.print(
                    f"[yellow]Terminated leftover process PID={old_pid}[/yellow]", highlight=False
                )
        except (ValueError, ProcessLookupError, PermissionError, OSError):
            pass
        with contextlib.suppress(OSError):
            pid_file.unlink()

    # Method 2: Scan all Python processes to find blender-mcp-ai related ones
    if sys.platform == "win32":
        killed += _cleanup_windows(current_pid)
    else:
        killed += _cleanup_unix(current_pid)

    return killed


def _is_blender_mcp_process(pid: int) -> bool:
    """Check if the specified PID is a blender-mcp-ai process"""
    try:
        if sys.platform == "win32":
            import subprocess

            result = subprocess.run(
                ["wmic", "process", "where", f"ProcessId={pid}", "get", "CommandLine", "/value"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return "blender-mcp-ai" in result.stdout or "blender_mcp" in result.stdout
        else:
            cmdline_path = f"/proc/{pid}/cmdline"
            if os.path.exists(cmdline_path):
                with open(cmdline_path) as f:
                    cmdline = f.read()
                return "blender-mcp-ai" in cmdline or "blender_mcp" in cmdline
    except Exception:
        pass
    return False


def _cleanup_windows(current_pid: int) -> int:
    """Clean up zombie processes on Windows"""
    killed = 0
    try:
        import subprocess

        result = subprocess.run(
            [
                "wmic",
                "process",
                "where",
                "Name='python.exe'",
                "get",
                "ProcessId,CommandLine",
                "/value",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Parse WMIC output
        entries = result.stdout.split("\n\n")
        pid = None
        cmdline = ""

        for entry in entries:
            for line in entry.strip().split("\n"):
                line = line.strip()
                if line.startswith("CommandLine="):
                    cmdline = line[len("CommandLine=") :]
                elif line.startswith("ProcessId="):
                    try:
                        pid = int(line[len("ProcessId=") :])
                    except ValueError:
                        pid = None

            if (
                pid
                and pid != current_pid
                and ("blender-mcp-ai" in cmdline or "blender_mcp" in cmdline)
            ):
                try:
                    os.kill(pid, signal.SIGTERM)
                    killed += 1
                    console.print(
                        f"[yellow]Terminated leftover process PID={pid}[/yellow]", highlight=False
                    )
                except (ProcessLookupError, PermissionError, OSError):
                    pass

            pid = None
            cmdline = ""
    except Exception:
        pass
    return killed


def _cleanup_unix(current_pid: int) -> int:
    """Clean up zombie processes on Unix/macOS"""
    killed = 0
    try:
        import subprocess

        result = subprocess.run(
            ["pgrep", "-f", "blender.mcp"], capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            try:
                pid = int(line.strip())
                if pid != current_pid:
                    os.kill(pid, signal.SIGTERM)
                    killed += 1
                    console.print(
                        f"[yellow]Terminated leftover process PID={pid}[/yellow]", highlight=False
                    )
            except (ValueError, ProcessLookupError, PermissionError, OSError):
                pass
    except Exception:
        pass
    return killed


def _write_pid_file() -> None:
    """Write the current process PID file"""
    try:
        pid_file = _get_pid_file()
        pid_file.write_text(str(os.getpid()))
    except OSError:
        pass


def _remove_pid_file() -> None:
    """Remove the PID file"""
    try:
        pid_file = _get_pid_file()
        if pid_file.exists():
            pid_file.unlink()
    except OSError:
        pass


def setup_logging(level: str) -> None:
    """Configure logging system (output to stderr to avoid interfering with MCP stdio)"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True, show_path=False)],
    )


@click.group(invoke_without_command=True)
@click.option("--host", default=config.BLENDER_HOST, help="Blender connection host")
@click.option("--port", default=config.BLENDER_PORT, help="Blender connection port")
@click.option(
    "--transport", default="stdio", type=click.Choice(["stdio", "http"]), help="Transport mode"
)
@click.option("--http-port", default=config.MCP_HTTP_PORT, help="HTTP server port")
@click.option(
    "--log-level",
    default=config.LOG_LEVEL,
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    help="Log level",
)
@click.version_option(version=__version__, prog_name="blender-mcp-ai")
@click.pass_context
def main(
    ctx: click.Context, host: str, port: int, transport: str, http_port: int, log_level: str
) -> None:
    """Blender MCP - Blender control interface for AI assistants

    Enables AI assistants to directly control Blender via the MCP protocol,
    supporting creation of 3D models, characters, animations, and scenes.
    """
    if ctx.invoked_subcommand is None:
        setup_logging(log_level)

        # === Clean up zombie processes before startup ===
        killed = _cleanup_zombie_processes()
        if killed > 0:
            console.print(f"[yellow]Cleaned up {killed} leftover process(es)[/yellow]")

        # === Write PID file + register exit hook ===
        _write_pid_file()
        atexit.register(_remove_pid_file)

        server = BlenderMCPServer(blender_host=host, blender_port=port)

        try:
            if transport == "stdio":
                # stdio mode: stdout used for MCP protocol, logs go to stderr
                console.print("[green]Starting Blender MCP server (stdio mode)[/green]")
                console.print(f"[dim]Blender connection: {host}:{port} | PID: {os.getpid()}[/dim]")
                server.run_stdio()  # synchronous call
            else:
                console.print("[green]Starting Blender MCP server (HTTP mode)[/green]")
                console.print(f"[dim]HTTP port: {http_port}[/dim]")
                console.print(f"[dim]Blender connection: {host}:{port} | PID: {os.getpid()}[/dim]")
                server.run_http(http_port)  # synchronous call
        except KeyboardInterrupt:
            console.print("\n[yellow]Server stopped[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
        finally:
            _remove_pid_file()


@main.command()
@click.option("--blender-path", default=None, help="Blender installation path")
@click.option("--force", is_flag=True, help="Force reinstall")
def install_addon(blender_path: str | None, force: bool) -> None:
    """Install the Blender addon

    Automatically detects the Blender installation path and installs the MCP addon.
    """
    from blender_mcp.installer import install_blender_addon

    try:
        result = install_blender_addon(blender_path, force)
        if result:
            console.print("[green]✓ Blender addon installed successfully![/green]")
            console.print("[dim]Please restart Blender and enable the addon in Preferences[/dim]")
        else:
            console.print("[yellow]Addon already exists, use --force to reinstall[/yellow]")
    except Exception as e:
        console.print(f"[red]Installation failed: {e}[/red]")
        sys.exit(1)


@main.command()
def check() -> None:
    """Check Blender connection status"""
    from blender_mcp.connection import BlenderConnection

    console.print("[dim]Checking Blender connection...[/dim]")

    async def do_check() -> None:
        conn = BlenderConnection()
        try:
            await conn.connect()
            info = await conn.get_blender_info()
            console.print("[green]✓ Blender connection OK[/green]")
            console.print(f"  Version: {info.get('version', 'unknown')}")
            console.print(f"  Scene: {info.get('scene', 'unknown')}")
            await conn.disconnect()
        except Exception as e:
            console.print(f"[red]✗ Connection failed: {e}[/red]")
            console.print(
                "[dim]Please ensure Blender is running and the MCP addon is enabled[/dim]"
            )

    asyncio.run(do_check())


if __name__ == "__main__":
    main()
