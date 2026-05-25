from __future__ import annotations
import json
from openai import OpenAI
from rich.console import Console
from .tools import TOOLS, execute_tool

SYSTEM_PROMPT = """You are Anvar GPT — a powerful terminal AI agent, like Claude Code.

You help users with:
- Writing, reading, and editing code and files
- Running shell commands and debugging errors
- Explaining concepts and answering questions
- Building projects from scratch

You have access to tools: read_file, write_file, create_file, list_directory, run_command.
Use them proactively when it makes sense — don't ask, just act.
Be concise, direct, and technically precise. Terminal style."""


class Agent:
    def __init__(self, config: dict) -> None:
        self.client  = OpenAI(api_key=config["api_key"], base_url=config["base_url"])
        self.model   = config["model"]
        self.history: list[dict] = []

    def set_model(self, model: str) -> None:
        self.model = model

    def clear_history(self) -> None:
        self.history = []

    def chat(self, user_input: str, console: Console) -> None:
        self.history.append({"role": "user", "content": user_input})
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + self.history

        for _ in range(10):   # max 10 tool-call rounds
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=TOOLS,
                    tool_choice="auto",
                    stream=True,
                )
            except Exception as e:
                console.print(f"\n[red]API error: {e}[/red]\n")
                return

            text_chunks: list[str]       = []
            tool_calls_raw: dict         = {}
            finish_reason: str | None    = None
            streaming_started            = False

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
            if full_text:
                console.print()

            # No tool calls → done
            if finish_reason != "tool_calls" or not tool_calls_raw:
                if full_text:
                    self.history.append({"role": "assistant", "content": full_text})
                console.print()
                return

            # Build assistant message with tool_calls
            tool_calls_list = [
                {
                    "id": tool_calls_raw[i]["id"],
                    "type": "function",
                    "function": {
                        "name":      tool_calls_raw[i]["name"],
                        "arguments": tool_calls_raw[i]["arguments"],
                    },
                }
                for i in sorted(tool_calls_raw)
            ]
            messages.append({"role": "assistant", "content": full_text or None, "tool_calls": tool_calls_list})

            # Execute tools
            console.print()
            for tc in tool_calls_list:
                name   = tc["function"]["name"]
                args   = tc["function"]["arguments"]
                preview = self._preview_args(args)
                console.print(f"[dim green]  >> {name}({preview})[/dim green]")
                result = execute_tool(name, args)
                short  = result[:120] + ("…" if len(result) > 120 else "")
                console.print(f"[dim]    → {short}[/dim]")
                messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})

            console.print()

        console.print("[yellow]Reached max tool iterations.[/yellow]\n")

    @staticmethod
    def _preview_args(arguments: str) -> str:
        try:
            d = json.loads(arguments)
            parts = []
            for k, v in d.items():
                s = str(v)
                parts.append(f"{k}={s[:40]!r}" if len(s) > 40 else f"{k}={s!r}")
            return ", ".join(parts)
        except Exception:
            return arguments[:60]
