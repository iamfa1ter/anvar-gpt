"""
AnvarGPT Local Bridge Server
Runs on localhost:7723 — lets the web terminal use YOUR machine.
Start with:  anvar serve
"""
from __future__ import annotations
import json, os, platform
from http.server import HTTPServer, BaseHTTPRequestHandler
from openai import OpenAI
from .tools import TOOLS, execute_tool
from .agent import SYSTEM_PROMPT

PORT     = 7723
_OR_BASE = "https://openrouter.ai/api/v1"

_TOOL_COLOR = {
    "bash":           "cyan",
    "read_file":      "blue",
    "write_file":     "green",
    "edit_file":      "yellow",
    "list_directory": "blue",
    "glob_files":     "magenta",
    "grep_files":     "magenta",
}


def _make_client(api_key: str) -> OpenAI:
    return OpenAI(
        api_key=api_key,
        base_url=_OR_BASE,
        default_headers={
            "HTTP-Referer": "https://anvargpt.vercel.app",
            "X-Title": "Anvar GPT Local",
        },
    )


def _run_agent(user_input: str, model: str, history: list, api_key: str) -> list:
    """Full tool-calling loop — runs on this machine, returns list of line dicts."""
    client = _make_client(api_key)
    lines  = []

    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in (history or [])[-20:]:
        msgs.append({"role": h["role"], "content": h["content"]})
    msgs.append({"role": "user", "content": user_input})

    while True:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=msgs,
                tools=TOOLS,
                tool_choice="auto",
                stream=False,
            )
        except Exception as e:
            lines.append({"type": "err", "text": f"API error: {e}"})
            return lines

        choice     = response.choices[0]
        msg        = choice.message
        finish     = choice.finish_reason
        text       = msg.content or ""
        tool_calls = msg.tool_calls or []

        if text:
            for ln in text.split("\n"):
                lines.append({"type": "out", "text": ln})

        if finish != "tool_calls" or not tool_calls:
            if text:
                msgs.append({"role": "assistant", "content": text})
            break

        msgs.append({
            "role":       "assistant",
            "content":    text or None,
            "tool_calls": [
                {
                    "id":   tc.id,
                    "type": "function",
                    "function": {
                        "name":      tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in tool_calls
            ],
        })

        for tc in tool_calls:
            name    = tc.function.name
            args_js = tc.function.arguments
            color   = _TOOL_COLOR.get(name, "cyan")

            try:
                d = json.loads(args_js)
                parts = []
                for k, v in d.items():
                    s = str(v).replace("\n", "\\n")
                    parts.append(f"{k}={s[:50]!r}" if len(s) > 50 else f"{k}={s!r}")
                preview = ", ".join(parts)
            except Exception:
                preview = args_js[:80]

            lines.append({"type": "tool_call", "text": f"{name}({preview})", "color": color})

            result       = execute_tool(name, args_js)
            result_lines = result.splitlines()
            for rl in result_lines[:40]:
                lines.append({"type": "tool_result", "text": rl})
            if len(result_lines) > 40:
                lines.append({"type": "tool_result", "text": f"  … ({len(result_lines)-40} more lines)"})

            msgs.append({
                "role":         "tool",
                "tool_call_id": tc.id,
                "content":      result,
            })

    return lines


class _Handler(BaseHTTPRequestHandler):
    api_key: str = ""
    model: str   = ""

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def _json(self, status: int, data: dict):
        body = json.dumps(data).encode()
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/health", "/api/health"):
            self._json(200, {
                "status": "ok",
                "mode":   "local",
                "os":     platform.system(),
                "cwd":    os.getcwd(),
                "host":   platform.node(),
            })
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        if self.path not in ("/api/agent", "/agent"):
            self._json(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            body   = json.loads(self.rfile.read(length))
        except Exception:
            self._json(400, {"error": "bad request"})
            return

        user_input = body.get("message", "").strip()
        model      = body.get("model") or self.model or "openai/gpt-oss-120b:free"
        history    = body.get("history") or []

        if not user_input:
            self._json(400, {"error": "message required"})
            return

        lines = _run_agent(user_input, model, history, self.api_key)
        self._json(200, {"lines": lines, "type": "local"})

    def log_message(self, *args): pass


def start(api_key: str, model: str, console=None) -> None:
    """Start the blocking HTTP bridge. Run in main thread (blocks until Ctrl+C)."""
    _Handler.api_key = api_key
    _Handler.model   = model

    server = HTTPServer(("localhost", PORT), _Handler)

    if console:
        from rich.panel import Panel
        console.print(Panel(
            f"[bold green]Local bridge active[/bold green]\n\n"
            f"  [dim]port  [/dim][green]{PORT}[/green]\n"
            f"  [dim]os    [/dim][green]{platform.system()} · {platform.node()}[/green]\n"
            f"  [dim]cwd   [/dim][green]{os.getcwd()}[/green]\n\n"
            f"  Open [cyan]https://anvargpt.vercel.app[/cyan]\n"
            f"  [dim]The Terminal tab will auto-connect to your machine.[/dim]\n\n"
            f"  [dim]Ctrl+C to stop[/dim]",
            title="[bold green]anvar serve[/bold green]",
            border_style="green",
            padding=(1, 3),
        ))
    else:
        print(f"anvar serve · http://localhost:{PORT}  (Ctrl+C to stop)")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        if console:
            console.print("\n[dim]Bridge stopped.[/dim]")
        server.server_close()
