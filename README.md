# stop-the-army

Personal skills and always-on instructions, packaged as one plugin that
installs in **Claude Code**, **GitHub Copilot** (CLI and VS Code), **OpenAI
Codex**, **Cursor** and **Gemini CLI**, on **Linux, macOS and Windows**.

Nothing to install at runtime: no Python, no Node, no WSL. Hooks use only
the shell each harness already runs (sh/bash, Git Bash or PowerShell).

## Editing this repo

**Edit only these, then commit and push. Nothing else to run:**

| To change | Edit |
|---|---|
| your always-on instructions | `INSTRUCTIONS.md` |
| a skill | `skills/<name>/SKILL.md` (folder name = `name:` in the file) |
| name, version, description, author | `plugin.json` (repo root) |

On every push, CI (`.github/workflows/validate.yml`) regenerates all the
harness-specific files and commits them back as `github-actions[bot]`, then
tests the hooks on real Linux, macOS and Windows machines. **Run `git pull`
before your next edit** to pick up that bot commit.

Every generated file is marked: the manifests start with a
`"//": "GENERATED FILE - DO NOT EDIT HERE"` banner (JSON has no comments),
and the hook payloads have `.generated.` in their filename. They get no
banner because four different tools parse them at runtime.

Optional, to test locally before pushing (needs Python on that machine only):

```sh
python3 scripts/sync.py && python3 scripts/test_hooks.py
claude --plugin-dir .            # try it in a real session
```

`claude plugin validate .` passes, with one "Unknown field '//'" warning per
banner, so don't use `--strict`.

## Layout

```
plugin.json                        EDIT  Agent Plugins 1.0 manifest → Copilot, VS Code, Codex, Cursor
INSTRUCTIONS.md                    EDIT  personal instructions, injected into every session
skills/*/SKILL.md                  EDIT  Agent Skills, read by every harness
hooks/hooks.json                   hand-written SessionStart hook → Claude Code, Codex, Gemini CLI
com.github.copilot/hooks/hooks.json  hand-written sessionStart hook → Copilot CLI / VS Code
hooks/session-start.generated.json   generated hook payload (Claude Code / Codex / Gemini)
com.github.copilot/hooks/session-start.generated.json  generated hook payload (Copilot)
.claude-plugin/plugin.json         generated → Claude Code
.claude-plugin/marketplace.json    generated → Claude Code / Copilot CLI / Codex marketplace
gemini-extension.json              generated → Gemini CLI
scripts/sync.py                    the generator (run by CI; --check for pull requests)
scripts/test_hooks.py              runs every hook in every shell present (CI)
scripts/link-skills.{sh,ps1}       fallback installer for harnesses without plugins
```

## How always-on instructions work

Plugins can't ship a `CLAUDE.md`/`AGENTS.md`, so a session-start hook injects
the instructions. To keep that hook trivial on every OS, `sync.py` does all
the work ahead of time: it strips HTML comments from `INSTRUCTIONS.md` and
writes the exact JSON each harness expects to `session-start.generated.json`. The JSON
is ASCII-only (accents become `é`), so Windows console encodings can't
corrupt it. At runtime the hook just prints that file:

| Harness | Linux / macOS | Windows |
|---|---|---|
| Claude Code | `hooks/hooks.json` `command`, line 1 (sh) | same `command`: line 1 under Git Bash, line 2 under PowerShell |
| Codex | `hooks/hooks.json` `command` (sh) | `hooks/hooks.json` `commandWindows` (PowerShell) |
| Copilot CLI / VS Code | `com.github.copilot/hooks/hooks.json` `bash` | same file, `powershell` |
| Gemini CLI | `hooks/hooks.json` `command` (bash) | same `command`, line 2 (PowerShell) |

**Why the shared `command` has two lines:** Claude Code on Windows runs hooks
in Git Bash if it's installed and PowerShell if not, and Gemini uses
PowerShell on Windows, so one string must work in both shells:

```
exec cat "${CLAUDE_PLUGIN_ROOT:-${extensionPath}}/hooks/session-start.generated.json"
$r = $env:CLAUDE_PLUGIN_ROOT; if (-not $r) { $r = '${extensionPath}' }; Get-Content -Raw ...
```

- **sh/bash** runs line 1. `exec` replaces the shell, so line 2 is never read.
- **PowerShell** doesn't know `exec`, so line 1 errors harmlessly (stderr only) and line 2 runs.
- `${extensionPath}` is filled in by Gemini, which doesn't set `CLAUDE_PLUGIN_ROOT`.

Hooks are inline commands, not `.ps1` files, so Windows' script execution
policy doesn't block them.

Notes:
- Keep it short: Claude Code caps injected context at 10,000 characters, and
  Codex budgets roughly 2,500 tokens. `sync.py` warns past 10,000.
- Codex asks you to trust a plugin hook the first time it runs, and again
  whenever the hook changes.
- Copilot CLI itself requires PowerShell 7 on Windows (its own prerequisite).

## Install

Push this repo to GitHub (private is fine; installs need `git clone` access
on that machine: SSH key or `gh auth login`). Replace `OWNER/REPO`:

| Harness | Command |
|---|---|
| Claude Code | `/plugin marketplace add OWNER/REPO` then `/plugin install stop-the-army@stop-the-army-marketplace` |
| Claude Code (local dev) | `claude --plugin-dir /path/to/this/repo` |
| Copilot CLI | `copilot plugin install OWNER/REPO` (or `/plugin marketplace add OWNER/REPO`) |
| VS Code (Copilot) | add the path to `chat.pluginLocations`, or the repo to `chat.plugins.marketplaces` |
| Codex | `codex plugin marketplace add OWNER/REPO` then `/plugins` |
| Gemini CLI | `gemini extensions install https://github.com/OWNER/REPO` (local: `gemini extensions link .`) |
| Anything else | `scripts/link-skills.sh <dir>` or `scripts\link-skills.ps1 <dir>`, then reference `INSTRUCTIONS.md` from the harness's global instructions |

Updates: `/plugin marketplace update` (Claude Code), `copilot plugin update`,
`gemini extensions update`. The new instructions apply from the next session.

`link-skills.ps1` is a script file, so on a default Windows install you may
need `powershell -ExecutionPolicy Bypass -File scripts\link-skills.ps1`.
It's only for harnesses with no plugin support.

## Extending

- **New skill:** add `skills/<name>/SKILL.md` with `name: <name>` and a
  `description` saying *when* to use it, then push (CI validates it).
- **Harness-specific extras** (subagents, slash commands, other hooks) aren't portable:
  - Claude Code: `agents/*.md`, `commands/*.md`, more entries in `hooks/hooks.json`
  - Copilot / VS Code: `com.github.copilot/{agents,commands,hooks}/`
  - Gemini CLI: `commands/*.toml`

  Any new hook must also work on Windows. Add a case to `scripts/test_hooks.py`.
