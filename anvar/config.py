from __future__ import annotations
import json
import os
from pathlib import Path


DEFAULTS = {
    "api_key":  os.environ.get("OPENROUTER_API_KEY", ""),
    "model":    "openai/gpt-oss-120b",
    "base_url": "https://openrouter.ai/api/v1",
}


def load_config() -> dict:
    # Allow override via local config file if user wants their own key
    cfg_file = Path.home() / ".anvar-gpt" / "config.json"
    if cfg_file.exists():
        try:
            data = json.loads(cfg_file.read_text(encoding="utf-8-sig"))
            if data.get("api_key"):
                return {**DEFAULTS, **data}
        except Exception:
            pass
    return dict(DEFAULTS)
