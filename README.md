# Anvar GPT — Terminal AI Agent

A Claude Code-style terminal agent powered by OpenRouter.

## Install (one line)

```bash
pip install git+https://github.com/YOUR_USERNAME/anvar-gpt.git
```

Then run from any terminal:

```bash
anvar
```

## First run

On first run it will ask for your OpenRouter API key.
Get one free at https://openrouter.ai/keys

Or set it as an environment variable to skip the prompt:

```
# Windows
set OPENROUTER_API_KEY=sk-or-v1-...

# Mac / Linux
export OPENROUTER_API_KEY=sk-or-v1-...
```

## What it can do

- Read and write files on your PC
- Run shell commands
- Write, fix, and explain code
- Answer any question
- Multi-turn conversation with memory

## Commands

| Command | Description |
|---|---|
| `/clear` | Clear conversation history |
| `/model ID` | Switch model (e.g. `/model openai/gpt-4o`) |
| `/ls` | List files in current directory |
| `/cwd` | Show current directory |
| `/exit` | Exit |

## Default model

`anthropic/claude-haiku-4-5` via OpenRouter
