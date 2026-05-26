"""AnvarGPT tools — filesystem + shell primitives for the agent."""
from __future__ import annotations
import glob as _glob
import json
import os
import re
import subprocess
from pathlib import Path


# ── OpenAI function-calling schemas ──────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": (
                "Run any shell command and return stdout + stderr. "
                "Use for running code, installing packages, git operations, etc. "
                "If the command starts with 'cd <path>' the working directory is changed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute"},
                    "timeout": {"type": "integer", "description": "Timeout seconds (default 60)"},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Read the contents of a file with line numbers. "
                "Optionally read only a specific range of lines."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path":       {"type": "string"},
                    "start_line": {"type": "integer", "description": "First line (1-indexed, inclusive)"},
                    "end_line":   {"type": "integer", "description": "Last line (inclusive)"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": (
                "Create a new file or fully overwrite an existing one. "
                "For small targeted changes use edit_file instead."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path":    {"type": "string"},
                    "content": {"type": "string", "description": "Complete file content"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": (
                "Surgical single-occurrence replacement inside an existing file. "
                "old_string must match exactly (including whitespace/indentation). "
                "Fails if old_string appears more than once — add more surrounding context. "
                "Always call read_file first to get the exact text."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path":       {"type": "string"},
                    "old_string": {"type": "string", "description": "Exact text to find"},
                    "new_string": {"type": "string", "description": "Replacement text"},
                },
                "required": ["path", "old_string", "new_string"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files and subdirectories.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory (default: current dir)"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "glob_files",
            "description": "Find files matching a glob pattern, e.g. '**/*.py' or 'src/*.ts'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "base":    {"type": "string", "description": "Base directory (default: current dir)"},
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grep_files",
            "description": "Search for a regex pattern inside files. Returns matching lines with file:line.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern":     {"type": "string", "description": "Regex pattern"},
                    "path":        {"type": "string", "description": "Dir or file to search (default: .)"},
                    "include":     {"type": "string", "description": "File filter e.g. '*.py'"},
                    "max_results": {"type": "integer", "description": "Max lines returned (default 100)"},
                },
                "required": ["pattern"],
            },
        },
    },
]


# ── Implementations ───────────────────────────────────────────────────────────

def bash(command: str, timeout: int = 60) -> str:
    stripped = command.strip()
    # Handle `cd` to actually change Python's cwd
    if re.match(r"^cd(\s|$)", stripped):
        target = stripped[2:].strip().strip('"').strip("'")
        target = os.path.expanduser(target) if target else os.path.expanduser("~")
        try:
            os.chdir(target)
            return f"cwd → {os.getcwd()}"
        except Exception as e:
            return f"[error] cd: {e}"
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True,
            text=True, timeout=timeout, cwd=os.getcwd(),
        )
        out = (result.stdout + result.stderr).rstrip()
        return out[:8000] if out else f"(exit {result.returncode})"
    except subprocess.TimeoutExpired:
        return f"[error] Timed out after {timeout}s"
    except Exception as e:
        return f"[error] {e}"


def read_file(path: str, start_line: int | None = None, end_line: int | None = None) -> str:
    try:
        lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    except FileNotFoundError:
        return f"[error] Not found: {path}"
    except Exception as e:
        return f"[error] {e}"

    total = len(lines)
    s = max(0, (start_line - 1) if start_line else 0)
    e = min(total, end_line if end_line else total)
    chunk = lines[s:e]

    truncated = len(chunk) > 500
    if truncated:
        chunk = chunk[:500]

    out = "\n".join(f"{s + i + 1:5} | {l}" for i, l in enumerate(chunk))
    if truncated:
        out += f"\n  ... ({total - s - 500} more lines -- use start_line/end_line)"
    return out or "(empty)"


def write_file(path: str, content: str) -> str:
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"Wrote {content.count(chr(10)) + 1} lines → {path}"
    except Exception as e:
        return f"[error] {e}"


def edit_file(path: str, old_string: str, new_string: str) -> str:
    try:
        content = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return f"[error] Not found: {path}"
    except Exception as e:
        return f"[error] {e}"

    if old_string not in content:
        return (
            f"[error] old_string not found in {path}\n"
            "Tip: call read_file first and copy the exact text including indentation."
        )
    count = content.count(old_string)
    if count > 1:
        return (
            f"[error] old_string appears {count}× — add more surrounding context to make it unique."
        )
    try:
        Path(path).write_text(content.replace(old_string, new_string, 1), encoding="utf-8")
        return f"Edited {path}"
    except Exception as e:
        return f"[error] {e}"


def list_directory(path: str = ".") -> str:
    try:
        entries = []
        for item in sorted(Path(path).iterdir()):
            if item.is_dir():
                entries.append(f"  [dir]  {item.name}/")
            else:
                sz = item.stat().st_size
                entries.append(f"  [file] {item.name}  ({sz:,} B)" if sz < 1024
                                else f"  [file] {item.name}  ({sz//1024:,} KB)")
        return "\n".join(entries) or "(empty)"
    except Exception as e:
        return f"[error] {e}"


def glob_files(pattern: str, base: str = ".") -> str:
    try:
        matches = sorted(_glob.glob(os.path.join(base, pattern), recursive=True))
        if not matches:
            return "(no matches)"
        if len(matches) > 200:
            return "\n".join(matches[:200]) + f"\n… ({len(matches)-200} more)"
        return "\n".join(matches)
    except Exception as e:
        return f"[error] {e}"


def grep_files(pattern: str, path: str = ".", include: str = "*", max_results: int = 100) -> str:
    try:
        rx = re.compile(pattern)
    except re.error as e:
        return f"[error] Invalid regex: {e}"

    p = Path(path)
    files = [p] if p.is_file() else sorted(p.rglob(include))
    results: list[str] = []

    for fp in files:
        if not fp.is_file():
            continue
        try:
            for i, line in enumerate(fp.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                if rx.search(line):
                    results.append(f"{fp}:{i}: {line.strip()}")
                    if len(results) >= max_results:
                        results.append(f"… (capped at {max_results})")
                        return "\n".join(results)
        except Exception:
            continue

    return "\n".join(results) if results else "(no matches)"


# ── Dispatcher ────────────────────────────────────────────────────────────────

def execute_tool(name: str, arguments: str) -> str:
    try:
        args = json.loads(arguments)
    except Exception:
        args = {}

    dispatch = {
        "bash":           lambda: bash(args.get("command", ""), args.get("timeout", 60)),
        "read_file":      lambda: read_file(args.get("path", ""), args.get("start_line"), args.get("end_line")),
        "write_file":     lambda: write_file(args.get("path", ""), args.get("content", "")),
        "edit_file":      lambda: edit_file(args.get("path", ""), args.get("old_string", ""), args.get("new_string", "")),
        "list_directory": lambda: list_directory(args.get("path", ".")),
        "glob_files":     lambda: glob_files(args.get("pattern", "*"), args.get("base", ".")),
        "grep_files":     lambda: grep_files(args.get("pattern", ""), args.get("path", "."), args.get("include", "*"), args.get("max_results", 100)),
    }
    fn = dispatch.get(name)
    return fn() if fn else f"[error] Unknown tool: {name}"
