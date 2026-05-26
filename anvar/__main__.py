#!/usr/bin/env python3
"""AnvarGPT — AI coding agent for your terminal."""
from __future__ import annotations
import io
import os
import sys
from pathlib import Path

# Force UTF-8 on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() not in ("utf-8", "utf8"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from rich.console import Console
from rich.text import Text
from .config import load_config
from .agent import Agent

VERSION = "2.0.0"

BANNER = """\
[bold green]
   █████╗ ███╗   ██╗██╗   ██╗ █████╗ ██████╗      ██████╗ ██████╗ ████████╗
  ██╔══██╗████╗  ██║██║   ██║██╔══██╗██╔══██╗    ██╔════╝ ██╔══██╗╚══██╔══╝
  ███████║██╔██╗ ██║██║   ██║███████║██████╔╝    ██║  ███╗██████╔╝   ██║
  ██╔══██║██║╚██╗██║╚██╗ ██╔╝██╔══██║██╔══██╗    ██║   ██║██╔═══╝    ██║
  ██║  ██║██║ ╚████║ ╚████╔╝ ██║  ██║██║  ██║    ╚██████╔╝██║        ██║
  ╚═╝  ╚═╝╚═╝  ╚═══╝  ╚═══╝  ╚═╝  ╚═╝╚═╝  ╚═╝     ╚═════╝ ╚═╝        ╚═╝
[/bold green]"""

HELP_TEXT = """
[bold green]Commands[/bold green]
  [cyan]/help[/cyan]            Show this help
  [cyan]/clear[/cyan]           Clear conversation history
  [cyan]/model [ID][/cyan]      Switch model  (e.g. /model openai/gpt-4o)
  [cyan]/models[/cyan]          List available models
  [cyan]/cd [path][/cyan]       Change working directory
  [cyan]/ls[/cyan]              List files in current directory
  [cyan]/cwd[/cyan]             Show current directory
  [cyan]/exit[/cyan]            Exit

[bold green]Tools the agent has[/bold green]
  [green]bash[/green]           Run any shell command
  [green]read_file[/green]      Read a file with line numbers
  [green]write_file[/green]     Create or overwrite a file
  [green]edit_file[/green]      Surgical text replacement (like Claude Code)
  [green]glob_files[/green]     Find files by pattern  (e.g. **/*.py)
  [green]grep_files[/green]     Search inside files by regex
  [green]list_directory[/green] List a directory

[bold green]Example prompts[/bold green]
  [dim]read main.py and explain what it does[/dim]
  [dim]find all TODO comments in this project[/dim]
  [dim]write a REST API with FastAPI and save it to api.py[/dim]
  [dim]run the tests and fix whatever's failing[/dim]
  [dim]refactor the login function to use async/await[/dim]
  [dim]what is the overall structure of this codebase?[/dim]
"""

AVAILABLE_MODELS = [
    ("openai/gpt-oss-120b:free",              "GPT OSS 120B  — default, free"),
    ("openai/gpt-4o",                          "GPT-4o        — best OpenAI (paid)"),
    ("anthropic/claude-opus-4",                "Claude Opus 4 — best overall (paid)"),
    ("anthropic/claude-sonnet-4-5",            "Claude Sonnet 4.5 (paid)"),
    ("meta-llama/llama-3.3-70b-instruct:free", "Llama 3.3 70B — free"),
    ("qwen/qwq-32b:free",                      "QwQ 32B — reasoning, free"),
]


def main() -> None:
    console = Console(force_terminal=True, highlight=False)
    config  = load_config()

    console.clear()
    console.print(BANNER)
    console.print(
        f"[dim]  v{VERSION}  ·  model=[green]{config['model']}[/green]"
        f"  ·  cwd=[green]{Path.cwd()}[/green][/dim]"
    )
    console.print("[dim]  Type /help for commands  ·  Ctrl+C or /exit to quit[/dim]\n")

    agent = Agent(config)

    while True:
        cwd_name = Path(os.getcwd()).name or os.getcwd()
        prompt = Text()
        prompt.append("anvar", style="bold green")
        prompt.append(f" {cwd_name}", style="dim green")
        prompt.append(" › ", style="bold green")

        try:
            user_input = console.input(prompt).strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye.[/dim]")
            sys.exit(0)

        if not user_input:
            continue

        lo = user_input.lower()

        if lo in ("/exit", "/quit", "/q"):
            console.print("[dim]Goodbye.[/dim]")
            sys.exit(0)

        if lo == "/help":
            console.print(HELP_TEXT)
            continue

        if lo == "/clear":
            console.clear()
            agent.clear_history()
            console.print("[dim]History cleared.[/dim]\n")
            continue

        if lo == "/cwd":
            console.print(f"[green]{os.getcwd()}[/green]\n")
            continue

        if lo == "/ls":
            from .tools import list_directory
            console.print(list_directory(".") + "\n")
            continue

        if lo == "/models":
            console.print("\n[bold green]Available models:[/bold green]")
            for mid, desc in AVAILABLE_MODELS:
                marker = "[green]●[/green] " if mid == agent.model else "  "
                console.print(f"  {marker}[cyan]{mid}[/cyan]  [dim]{desc}[/dim]")
            console.print()
            continue

        if lo.startswith("/model"):
            new_model = user_input[6:].strip()
            if new_model:
                agent.set_model(new_model)
                console.print(f"[green]Model → {new_model}[/green]\n")
            else:
                console.print(f"[green]Current: {agent.model}[/green]\n")
            continue

        if lo.startswith("/cd"):
            target = user_input[3:].strip() or os.path.expanduser("~")
            try:
                os.chdir(os.path.expanduser(target))
                console.print(f"[green]{os.getcwd()}[/green]\n")
            except Exception as e:
                console.print(f"[red]cd: {e}[/red]\n")
            continue

        if user_input.startswith("/"):
            console.print(f"[red]Unknown command: {user_input}  (try /help)[/red]\n")
            continue

        # ── Send to agent ─────────────────────────────────────────────────────
        agent.chat(user_input, console)


if __name__ == "__main__":
    main()
