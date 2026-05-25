#!/usr/bin/env python3
"""Anvar GPT — Terminal AI Agent"""
from __future__ import annotations
import sys
import io
from pathlib import Path

# Force UTF-8 on Windows so box-drawing / arrow chars don't crash
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() not in ("utf-8", "utf8"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from rich.console import Console
from .config import load_config
from .agent import Agent

BANNER = r"""[bold green]
    _    _   ___   ___  __     ____  ____ _____
   / \  | \ | \ \ / / \ \ /  / ___|  _ \_   _|
  / _ \ |  \| |\ V / _ \ V /| |  _| |_) || |
 / ___ \| |\  | | |/ ___ \| | | |_| |  __/ | |
/_/   \_\_| \_| |_/_/   \_\_|  \____|_|    |_|
[/bold green]"""

HELP_TEXT = """
[bold green]Commands:[/bold green]
  [cyan]/clear[/cyan]       Clear conversation history
  [cyan]/model ID[/cyan]    Switch model (e.g. /model openai/gpt-4o)
  [cyan]/cwd[/cyan]         Show current working directory
  [cyan]/ls[/cyan]          List files in current directory
  [cyan]/exit[/cyan]        Exit Anvar GPT

[bold green]What I can do:[/bold green]
  - Read and write files on your PC
  - Run shell commands
  - Write, fix, and explain code
  - Answer any question

[bold green]Example prompts:[/bold green]
  [dim]"read my main.py and explain what it does"[/dim]
  [dim]"create a REST API in Python with FastAPI"[/dim]
  [dim]"run the tests and fix any errors you find"[/dim]
  [dim]"what files are in this folder?"[/dim]
"""


def main() -> None:
    console = Console(force_terminal=True, highlight=False)

    config = load_config()

    console.clear()
    console.print(BANNER)
    console.print(
        f"[dim]  Anvar GPT v1.0  model=[green]{config['model']}[/green]  "
        f"cwd=[green]{Path.cwd()}[/green][/dim]"
    )
    console.print("[dim]  Type /help for commands  Ctrl+C to exit[/dim]\n")

    agent = Agent(config)

    while True:
        try:
            user_input = console.input("[bold green]anvar >[/bold green] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye.[/dim]")
            sys.exit(0)

        if not user_input:
            continue

        if user_input in ("/exit", "/quit", "/q"):
            console.print("[dim]Goodbye.[/dim]")
            sys.exit(0)

        if user_input == "/help":
            console.print(HELP_TEXT)
            continue

        if user_input == "/clear":
            console.clear()
            agent.clear_history()
            console.print("[dim]History cleared.[/dim]\n")
            continue

        if user_input == "/cwd":
            console.print(f"[green]{Path.cwd()}[/green]\n")
            continue

        if user_input == "/ls":
            from .tools import list_directory
            console.print(list_directory(".") + "\n")
            continue

        if user_input.startswith("/model "):
            new_model = user_input[7:].strip()
            agent.set_model(new_model)
            console.print(f"[green]Model → {new_model}[/green]\n")
            continue

        agent.chat(user_input, console)


if __name__ == "__main__":
    main()
