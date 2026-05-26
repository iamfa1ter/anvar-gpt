"""AnvarGPT agent — streaming tool-calling loop with Rich UI."""
from __future__ import annotations
import json, os
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.rule import Rule
from .tools import TOOLS, execute_tool

SYSTEM_PROMPT = """\
You are Anvar — a powerful AI software engineer running as a CLI agent on the user's computer.
You have direct access to their filesystem and can execute any shell command.

## How to work
- Take initiative: when asked to do something, DO it — don't explain, just act
- Always call read_file before editing an existing file
- Use edit_file for targeted changes; use write_file for new files or full rewrites
- After making changes, verify: re-read the file or run the code
- If a command fails, read the error carefully and fix it — iterate until it works
- Be concise: short explanations, show progress through actions

## Tool usage patterns
- Understand a codebase  → list_directory → glob_files → read_file key files
- Fix a bug              → read_file → edit_file → bash to verify
- Add a feature          → read relevant files → write/edit → bash tests
- Debug an error         → bash → read error → find cause → fix → bash again
- Find something         → grep_files or glob_files first

## Response style
- Lead with actions, not lengthy explanations
- After finishing, give a brief 1-2 sentence summary
- Ask clarifying questions only when truly blocked\
"""

# Tool name → border color
_TOOL_COLORS = {
    "bash":           "cyan",
    "read_file":      "blue",
    "write_file":     "green",
    "edit_file":      "yellow",
    "list_directory": "blue",
    "glob_files":     "magenta",
    "grep_files":     "magenta",
}


class Agent:
    def __init__(self, config: dict) -> None:
        self.client = OpenAI(
            api_key=config["api_key"],
            base_url=config["base_url"],
            default_headers={
                "HTTP-Referer": "https://anvargpt.vercel.app",
                "X-Title": "Anvar GPT",
            },
        )
        self.model   = config["model"]
        self.history: list[dict] = []

    def set_model(self, model: str) -> None:
        self.model = model

    def clear_history(self) -> None:
        self.history = []

    def chat(self, user_input: str, console: Console) -> None:
        self.history.append({"role": "user", "content": user_input})
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + self.history

        while True:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=TOOLS,
                    tool_choice="auto",
                    stream=True,
                )
            except Exception as e:
                console.print(Panel(
                    f"[red]{e}[/red]",
                    title="[red]API Error[/red]",
                    border_style="red",
                ))
                return

            text_chunks: list[str]    = []
            tool_calls_raw: dict      = {}
            finish_reason: str | None = None
            streaming_started         = False

            for chunk in response:
                choice = chunk.choices[0] if chunk.choices else None
                if not choice:
                    continue
                delta         = choice.delta
                finish_reason = choice.finish_reason or finish_reason

                if delta.content:
                    if not streaming_started:
                        console.print()
                        streaming_started = True
                    text_chunks.append(delta.content)
                    console.print(delta.content, end="", markup=False, highlight=False)

                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_raw:
                            tool_calls_raw[idx] = {"id": "", "name": "", "arguments": ""}
                        if tc.id:
                            tool_calls_raw[idx]["id"] = tc.id
                        if tc.function:
                            if tc.function.name:
                                tool_calls_raw[idx]["name"] += tc.function.name
                            if tc.function.arguments:
                                tool_calls_raw[idx]["arguments"] += tc.function.arguments

            full_text = "".join(text_chunks)
            if streaming_started:
                console.print()

            if finish_reason != "tool_calls" or not tool_calls_raw:
                if full_text:
                    self.history.append({"role": "assistant", "content": full_text})
                console.print()
                return

            tool_calls_list = [
                {
                    "id":   tool_calls_raw[i]["id"],
                    "type": "function",
                    "function": {
                        "name":      tool_calls_raw[i]["name"],
                        "arguments": tool_calls_raw[i]["arguments"],
                    },
                }
                for i in sorted(tool_calls_raw)
            ]
            messages.append({
                "role":       "assistant",
                "content":    full_text or None,
                "tool_calls": tool_calls_list,
            })

            # ── Render each tool call ─────────────────────────────────────────
            for tc in tool_calls_list:
                name    = tc["function"]["name"]
                args_js = tc["function"]["arguments"]
                color   = _TOOL_COLORS.get(name, "cyan")

                preview = _preview_args(args_js)

                console.print(Panel(
                    f"[dim]{preview}[/dim]",
                    title=f"[bold {color}]{name}[/bold {color}]",
                    border_style=color + " dim",
                    padding=(0, 1),
                ))

                result = execute_tool(name, args_js)

                lines = result.splitlines()
                shown = lines[:30]
                for line in shown:
                    console.print(f"  [dim]{line}[/dim]")
                if len(lines) > 30:
                    console.print(f"  [dim]  ... ({len(lines)-30} more lines)[/dim]")
                console.print()

                messages.append({
                    "role":         "tool",
                    "tool_call_id": tc["id"],
                    "content":      result,
                })


def _preview_args(arguments: str) -> str:
    try:
        d = json.loads(arguments)
        parts = []
        for k, v in d.items():
            s = str(v).replace("\n", "\\n")
            parts.append(f"{k}={s[:60]!r}" if len(s) > 60 else f"{k}={s!r}")
        return ", ".join(parts)
    except Exception:
        return arguments[:80]
