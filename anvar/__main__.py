#!/usr/bin/env python3
"""AnvarGPT — AI coding agent for your terminal."""
from __future__ import annotations
import io, os, sys
from pathlib import Path

# Force UTF-8 on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() not in ("utf-8", "utf8"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from rich.console import Console
from rich.columns import Columns
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style as PtStyle
from prompt_toolkit.formatted_text import HTML

from .config import load_config
from .agent import Agent

VERSION = "2.1.0"

AVAILABLE_MODELS = [
    ("openai/gpt-oss-120b:free",              "GPT OSS 120B  — default, free"),
    ("openai/gpt-4o",                          "GPT-4o        — best OpenAI (paid)"),
    ("anthropic/claude-opus-4",                "Claude Opus 4 (paid)"),
    ("anthropic/claude-sonnet-4-5",            "Claude Sonnet 4.5 (paid)"),
    ("meta-llama/llama-3.3-70b-instruct:free", "Llama 3.3 70B — free"),
    ("qwen/qwq-32b:free",                      "QwQ 32B reasoning — free"),
]


def _welcome(console: Console, model: str) -> None:
    cwd = str(Path.cwd())

    left_body = Align.center(
        Text.assemble(
            ("\n", ""),
            ("A N V A R G P T\n", "bold green"),
            (f"v{VERSION}\n\n", "dim"),
            ("model  ", "dim"),   (model.split("/")[-1].replace(":free","") + "\n", "green"),
            ("dir    ", "dim"),   (Path(cwd).name + "\n", "green"),
            ("engine ", "dim"),   ("OpenRouter\n", "green"),
            ("\n", ""),
        )
    )

    right_body = Text.assemble(
        ("Tips for getting started\n\n", "bold"),
        ("/help   ", "cyan"),  ("show all commands\n", "dim"),
        ("/model  ", "cyan"),  ("switch AI model\n",   "dim"),
        ("/models ", "cyan"),  ("list models\n",       "dim"),
        ("/cd     ", "cyan"),  ("change directory\n",  "dim"),
        ("/clear  ", "cyan"),  ("clear history\n",     "dim"),
        ("/exit   ", "cyan"),  ("quit\n",              "dim"),
        ("\n", ""),
        ("What it can do\n\n", "bold"),
        ("read / write / edit files\n", "dim"),
        ("run any shell command\n",     "dim"),
        ("search code with grep/glob\n","dim"),
        ("fix bugs, write features\n",  "dim"),
    )

    left  = Panel(left_body,  border_style="green",    padding=(0, 3), expand=True)
    right = Panel(right_body, border_style="dim",      padding=(0, 2), expand=True)

    console.print(Columns([left, right], equal=True))
    console.print()


def main() -> None:
    console = Console(highlight=False)
    config  = load_config()

    console.clear()
    _welcome(console, config["model"])

    # Prompt toolkit session — saves history to disk
    hist_file = Path.home() / ".anvar-gpt" / "history"
    hist_file.parent.mkdir(parents=True, exist_ok=True)

    # prompt_toolkit needs a real terminal; fall back to plain input if piped
    use_pt = sys.stdin.isatty()
    session = None
    if use_pt:
        try:
            session = PromptSession(
                history=FileHistory(str(hist_file)),
                style=PtStyle.from_dict({
                    "anvar": "#00ff66 bold",
                    "path":  "#009933",
                    "arrow": "#00ff66 bold",
                }),
                mouse_support=False,
            )
        except Exception:
            use_pt = False

    def prompt_msg():
        name = Path(os.getcwd()).name or os.getcwd()
        return HTML(f"<anvar>anvar</anvar> <path>{name}</path><arrow> › </arrow>")

    agent = Agent(config)

    while True:
        try:
            if use_pt and session:
                user_input = session.prompt(prompt_msg).strip()
            else:
                cwd_name = Path(os.getcwd()).name or os.getcwd()
                user_input = console.input(f"[bold green]anvar[/bold green] [dim green]{cwd_name}[/dim green][bold green] › [/bold green]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye.[/dim]")
            sys.exit(0)

        if not user_input:
            continue

        lo = user_input.lower()

        # ── Built-in commands ─────────────────────────────────────────────────

        if lo in ("/exit", "/quit", "/q"):
            console.print("[dim]Goodbye.[/dim]")
            sys.exit(0)

        if lo == "/help":
            console.print(Panel(
                Text.assemble(
                    ("Commands\n\n",             "bold green"),
                    ("/help        ", "cyan"), ("this help\n",                "dim"),
                    ("/clear       ", "cyan"), ("clear conversation history\n","dim"),
                    ("/model [ID]  ", "cyan"), ("switch model\n",             "dim"),
                    ("/models      ", "cyan"), ("list all models\n",          "dim"),
                    ("/cd [path]   ", "cyan"), ("change directory\n",         "dim"),
                    ("/ls          ", "cyan"), ("list files here\n",          "dim"),
                    ("/cwd         ", "cyan"), ("show current path\n",        "dim"),
                    ("/exit        ", "cyan"), ("quit\n\n",                   "dim"),
                    ("Agent tools\n\n",            "bold green"),
                    ("bash         ", "green"), ("run any shell command\n",   "dim"),
                    ("read_file    ", "green"), ("read file with line nums\n","dim"),
                    ("write_file   ", "green"), ("create / overwrite file\n", "dim"),
                    ("edit_file    ", "green"), ("surgical text replace\n",   "dim"),
                    ("glob_files   ", "green"), ("find files by pattern\n",   "dim"),
                    ("grep_files   ", "green"), ("search inside files\n",     "dim"),
                    ("list_dir     ", "green"), ("list a directory\n",        "dim"),
                ),
                title="[bold green]AnvarGPT Help[/bold green]",
                border_style="green",
                padding=(1, 2),
            ))
            continue

        if lo == "/clear":
            console.clear()
            agent.clear_history()
            _welcome(console, agent.model)
            continue

        if lo == "/cwd":
            console.print(f"[green]{os.getcwd()}[/green]\n")
            continue

        if lo == "/ls":
            from .tools import list_directory
            console.print(Panel(list_directory("."), border_style="dim", title="[dim]ls[/dim]"))
            continue

        if lo == "/models":
            rows = []
            for mid, desc in AVAILABLE_MODELS:
                marker = "[green]●[/green]" if mid == agent.model else " "
                rows.append(f"  {marker} [cyan]{mid}[/cyan]  [dim]{desc}[/dim]")
            console.print(Panel(
                "\n".join(rows),
                title="[bold green]Models[/bold green]",
                border_style="green",
                padding=(1, 2),
            ))
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
            console.print(f"[red]Unknown command:[/red] {user_input}  [dim](try /help)[/dim]\n")
            continue

        # ── Agent ─────────────────────────────────────────────────────────────
        agent.chat(user_input, console)


if __name__ == "__main__":
    main()
