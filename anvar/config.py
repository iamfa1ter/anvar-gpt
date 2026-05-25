import json
import os
from pathlib import Path

CONFIG_DIR  = Path.home() / ".anvar"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS = {
    "api_key":  "",
    "model":    "openai/gpt-oss-120b",
    "base_url": "https://openrouter.ai/api/v1",
}


def load_config() -> dict:
    env_key = os.environ.get("OPENROUTER_API_KEY", "")
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text())
            if env_key:
                data["api_key"] = env_key
            return {**DEFAULTS, **data}
        except Exception:
            pass
    return {**DEFAULTS, "api_key": env_key}


def save_config(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


def setup_config(console) -> dict:
    console.print("\n[bold green]--- First-time setup -------------------------------------------[/bold green]")
    console.print("  Anvar GPT uses [cyan]OpenRouter[/cyan] to access AI models.")
    console.print("  Get a free key: [cyan]https://openrouter.ai/keys[/cyan]")
    console.print("[bold green]---------------------------------------------------------------[/bold green]\n")

    api_key = console.input("[bold green]Enter your OpenRouter API key:[/bold green] ").strip()
    if not api_key:
        console.print("[red]No key entered. Set OPENROUTER_API_KEY env var and retry.[/red]")
        raise SystemExit(1)

    cfg = {**DEFAULTS, "api_key": api_key}
    save_config(cfg)
    console.print(f"[dim]Config saved → {CONFIG_FILE}[/dim]\n")
    return cfg
