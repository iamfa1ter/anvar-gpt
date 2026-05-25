import json
import subprocess
from pathlib import Path

# ── Tool schemas (OpenAI function-calling format) ──────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the full contents of a file on disk.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write (or overwrite) a file on disk with given content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path":    {"type": "string", "description": "File path to write"},
                    "content": {"type": "string", "description": "Full file content"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files and folders in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path (default: current dir)"}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a shell command and return stdout + stderr.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute"}
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": "Create a new file with content. Fails if file already exists.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path":    {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
]


# ── Tool implementations ───────────────────────────────────────────────────

def read_file(path: str) -> str:
    try:
        text = Path(path).read_text(encoding="utf-8")
        lines = text.splitlines()
        if len(lines) > 300:
            text = "\n".join(lines[:300]) + f"\n... ({len(lines)-300} more lines)"
        return text
    except Exception as e:
        return f"[error] {e}"


def write_file(path: str, content: str) -> str:
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"Wrote {len(content):,} chars to {path}"
    except Exception as e:
        return f"[error] {e}"


def create_file(path: str, content: str) -> str:
    p = Path(path)
    if p.exists():
        return f"[error] File already exists: {path}"
    return write_file(path, content)


def list_directory(path: str = ".") -> str:
    try:
        entries = []
        for item in sorted(Path(path).iterdir()):
            if item.is_dir():
                entries.append(f"[dir]  {item.name}/")
            else:
                size = item.stat().st_size
                entries.append(f"[file] {item.name}  ({size:,} B)")
        return "\n".join(entries) or "(empty)"
    except Exception as e:
        return f"[error] {e}"


def run_command(command: str) -> str:
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        out = (result.stdout + result.stderr).strip()
        return out[:4000] if out else "(no output)"
    except subprocess.TimeoutExpired:
        return "[error] Timed out after 30s"
    except Exception as e:
        return f"[error] {e}"


def execute_tool(name: str, arguments: str) -> str:
    try:
        args = json.loads(arguments)
    except Exception:
        args = {}
    if name == "read_file":
        return read_file(args.get("path", ""))
    if name == "write_file":
        return write_file(args.get("path", ""), args.get("content", ""))
    if name == "create_file":
        return create_file(args.get("path", ""), args.get("content", ""))
    if name == "list_directory":
        return list_directory(args.get("path", "."))
    if name == "run_command":
        return run_command(args.get("command", ""))
    return f"[error] Unknown tool: {name}"
