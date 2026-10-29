# Anvar CLI — AI coding agent for your terminal

A Claude Code-style agent that reads and writes files, runs commands and fixes code on your computer.
It ships as a native app — no Python, Node or API keys needed — and comes with 32 AI models from
Cloudflare and NVIDIA through https://anvargpt.vercel.app.

## Install

**Windows (PowerShell)**

```powershell
irm https://anvargpt.vercel.app/install.ps1 | iex
```

**Windows (CMD)**

```bat
curl -fsSL https://anvargpt.vercel.app/install.cmd -o install.cmd && install.cmd && del install.cmd
```

**macOS / Linux**

```bash
curl -fsSL https://anvargpt.vercel.app/install.sh | bash
```

The installer downloads the build for your system from the
[latest release](https://github.com/iamfa1ter/anvar-gpt/releases/latest), checks its SHA-256 checksum
and puts `anvar` on your PATH. Open a new terminal afterwards.

## Use

```bash
anvar                  # interactive session
anvar -p "fix the failing test"   # one prompt, then exit
anvar serve            # let the Terminal on anvargpt.vercel.app use this computer
anvar update           # install the latest version
```

Inside a session:

| Command | Description |
|---|---|
| `/models` | list all 32 models |
| `/model <name>` | switch model, e.g. `/model gpt-oss-120b` |
| `/effort <level>` | low, medium, high, xhigh, max, ultracode |
| `/compact`, `/context`, `/usage` | manage the conversation |
| `/review`, `/security-review` | review uncommitted changes |
| `/help` | everything else |

## Web terminal

`anvar serve` starts a bridge on `localhost:7723` so the Terminal on https://anvargpt.vercel.app can run
commands and the AI agent on your machine. It only accepts requests from that site. Chrome asks once
for permission to reach apps on your local network — click Allow.

## Python version

The Python package in this repository (`pip install git+https://github.com/iamfa1ter/anvar-gpt.git`)
still works, but the native app above is the recommended way to install.
