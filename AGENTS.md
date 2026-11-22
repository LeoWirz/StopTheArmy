# Working on this repo

A personal cross-harness AI plugin: skills + always-on instructions. See README.md.

- Only edit the sources: `plugin.json`, `INSTRUCTIONS.md`, `skills/`, `hooks/hooks.json`, `com.github.copilot/hooks/hooks.json`.
- Never hand-edit generated files: anything starting with a `"//": "GENERATED FILE"` banner (`.claude-plugin/*`, `gemini-extension.json`) or named `*.generated.json`.
- CI regenerates and commits generated files on push. To verify locally before pushing, run: `python3 scripts/sync.py && python3 scripts/test_hooks.py`.
- `INSTRUCTIONS.md` is the owner's personal always-on instructions. Don't put repo-dev notes there.
- Hard requirement: the installed plugin must work natively on Windows, Linux and macOS with no runtime dependencies. Never add Python, Node or any other interpreter to hooks. Hook commands may only use sh/bash and PowerShell 5.1+ builtins. Python is allowed only in `scripts/` (dev and CI).
- Skill directory name must equal the `name:` in its SKILL.md frontmatter.
- Bump `version` in `plugin.json` for releases.
