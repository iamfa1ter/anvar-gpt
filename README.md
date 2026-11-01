# Anvar GPT CLI

An AI coding agent for your terminal, in hacker green. It reads and edits your
files, runs commands, and understands photos and documents. 32 free models
work out of the box, with no sign-up.

```
 █████╗ ███╗   ██╗██╗   ██╗ █████╗ ██████╗      ██████╗ ██████╗ ████████╗
██╔══██╗████╗  ██║██║   ██║██╔══██╗██╔══██╗    ██╔════╝ ██╔══██╗╚══██╔══╝
███████║██╔██╗ ██║██║   ██║███████║██████╔╝    ██║  ███╗██████╔╝   ██║
██╔══██║██║╚██╗██║╚██╗ ██╔╝██╔══██║██╔══██╗    ██║   ██║██╔═══╝    ██║
██║  ██║██║ ╚████║ ╚████╔╝ ██║  ██║██║  ██║    ╚██████╔╝██║        ██║
╚═╝  ╚═╝╚═╝  ╚═══╝  ╚═══╝  ╚═╝  ╚═╝╚═╝  ╚═╝     ╚═════╝ ╚═╝        ╚═╝
```

## Install

| System | Command |
|---|---|
| Windows (PowerShell) | `irm https://anvargpt.vercel.app/install.ps1 \| iex` |
| Windows (CMD) | `curl -fsSL https://anvargpt.vercel.app/install.cmd -o install.cmd && install.cmd && del install.cmd` |
| macOS / Linux | `curl -fsSL https://anvargpt.vercel.app/install.sh \| bash` |

You can also download a binary from the
[latest release](https://github.com/iamfa1ter/anvar-gpt/releases/latest) or the
Anvar CLI page on https://anvargpt.vercel.app. Each download has a SHA-256 checksum.

Then open a terminal in any folder and run `anvar`.

## Using it

| Shortcut | What it does |
|---|---|
| `enter` | send (`ctrl+j` or `\` then enter starts a new line) |
| `tab` | switch agent: **Build** (edits files, runs commands) or **Plan** (read-only) |
| `ctrl+p` | command palette |
| `/` | commands and skills |
| `@` | attach a file from this folder |
| drag & drop | attach photos, PDF, Word, Excel, PowerPoint, code, audio |
| `alt+v` · `/paste` | attach an image from the clipboard |
| `!command` | run a shell command yourself |
| `esc` | stop the answer |
| mouse drag | select text — it is copied automatically (`ctrl+c` copies it too) |
| **copy** button | under every answer — copies the whole answer |
| `ctrl+n` · **+ New chat** | start a new chat; the old one is saved |
| `ctrl+r` · **☰ Chats** | open a saved chat — `anvar -c` reopens the last one |
| `ctrl+o` · `ctrl+t` | full tool output · model reasoning |

## Commands

| Command | What it does |
|---|---|
| `/models` | switch model; 32 free models, plus any provider you connect |
| `/connect` | connect your own provider account: OpenAI, Anthropic, Gemini, NVIDIA, Cloudflare, Groq, OpenRouter, DeepSeek, Mistral, xAI, Together, or any OpenAI-compatible server (Ollama, LM Studio…) |
| `/prompt` | view or edit the base system prompt, or the per-project `ANVAR.md` |
| `/skills` | list skills; `/skills new <name>` creates your own |
| `/themes` | Hacker Green, Matrix, Classic, Transparent |
| `/effort` | reasoning effort: low · medium · high · xhigh · max · ultracode |
| `/chats` · `/new` | open a saved chat · start a new one |
| `/mouse` | turn mouse capture off to use your terminal's own selection |
| `/undo` | undo the file changes from the last answer |
| `/compact` | summarize the conversation to free up context |
| `/copy` · `/export` | copy the last answer · save the chat as Markdown |
| `/status` · `/help` | current settings · everything above |

## Skills

Built-in skills: `/init`, `/review`, `/security-review`, `/simplify`, `/verify`, `/fix`,
`/test`, `/explain`, `/docs`, `/refactor`, `/optimize`, `/commit`, `/pr-description`.

A skill is a Markdown file in `~/.anvar-gpt/skills/` (for every project) or
`.anvar/skills/` (for one project):

```markdown
---
description: deploy the app
---
Build the project and deploy it to $ARGUMENTS. Report the URL.
```

Run it as `/deploy staging`.

## Scripts

```bash
anvar run "explain what this repo does"
anvar run -f screenshot.png "what is wrong here?"
git diff | anvar run --plan "review this diff"
anvar models
anvar update
```

## Where things are stored

`~/.anvar-gpt/`: `config.json` for settings, `auth.json` for the providers you connect
(they stay on this computer), `sessions/`, `skills/`, `ANVAR.md`.

Created by Anvar Ualikhanov.
