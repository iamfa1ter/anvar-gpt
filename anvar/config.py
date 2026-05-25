from __future__ import annotations
import json
from pathlib import Path

CONFIG_DIR  = Path.home() / ".anvar-gpt"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS = {
    "model":    "openai/gpt-oss-120b",
    "base_url": "https://openrouter.ai/api/v1",
}


def load_config() -> dict:
    if CONFIG_FILE.exists():
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        if data.get("api_key"):
            return {**DEFAULTS, **data}

    # First run — ask once, save forever
    print("\n  Anvar GPT — first-time setup")
    print("  Get your free key at: https://openrouter.ai/keys\n")
    key = input("  Paste your OpenRouter API key: ").strip()
    if not key:
        raise SystemExit("No key provided. Exiting.")

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({"api_key": key}, indent=2), encoding="utf-8")
    print(f"  Key saved to {CONFIG_FILE}\n")

    return {**DEFAULTS, "api_key": key}
