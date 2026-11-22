#!/usr/bin/env python3
"""Generate harness-specific files from the portable sources.

Dev-time only: installed plugins never run Python. All the work happens here,
so the session-start hooks only have to print a ready-made file.

Sources of truth (edit these):
  plugin.json       Agent Plugins 1.0 manifest -> Copilot CLI, VS Code, Codex, Cursor
  INSTRUCTIONS.md   personal always-on instructions
  skills/           Agent Skills

Generated (never edit by hand; CI regenerates and commits them on every push):
  .claude-plugin/plugin.json                             Claude Code manifest
  .claude-plugin/marketplace.json                        marketplace for Claude Code / Copilot CLI / Codex
  gemini-extension.json                                  Gemini CLI extension manifest
  hooks/session-start.generated.json                     hook payload: Claude Code, Codex, Gemini CLI
  com.github.copilot/hooks/session-start.generated.json  hook payload: Copilot CLI / VS Code

Hand-written, harness-specific (not generated):
  hooks/hooks.json                       SessionStart hook: Claude Code, Codex, Gemini CLI
  com.github.copilot/hooks/hooks.json    SessionStart hook: Copilot CLI / VS Code

Usage:  python3 scripts/sync.py           # write files
        python3 scripts/sync.py --check   # exit 1 if anything is stale or invalid (CI)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
META_KEYS = ["name", "version", "description", "author", "homepage", "repository", "license", "keywords"]
CONTEXT_WARN_CHARS = 10_000  # Claude Code truncates injected context beyond this


class SyncError(Exception):
    pass


def validate(plugin):
    if plugin.get("$schema") != PLUGIN_SCHEMA:
        raise SyncError(f"plugin.json $schema must be {PLUGIN_SCHEMA}")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", plugin.get("name", "")):
        raise SyncError("plugin.json name must be kebab-case")
    for skill_dir in sorted((ROOT / "skills").iterdir()):
        if not skill_dir.is_dir():
            continue
        md = skill_dir / "SKILL.md"
        if not md.exists():
            raise SyncError(f"{skill_dir.relative_to(ROOT)} has no SKILL.md")
        m = re.match(r"---\r?\n(.*?)\r?\n---\r?\n?", md.read_text(encoding="utf-8"), re.S)
        fm = dict(re.findall(r"^(\w+):\s*(.+?)\s*$", m.group(1), re.M)) if m else {}
        if fm.get("name") != skill_dir.name:
            raise SyncError(f"{md.relative_to(ROOT)}: frontmatter name must equal directory name '{skill_dir.name}'")
        if not fm.get("description"):
            raise SyncError(f"{md.relative_to(ROOT)}: frontmatter needs a description")


def load_instructions():
    path = ROOT / "INSTRUCTIONS.md"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S).strip()
    if len(text) > CONTEXT_WARN_CHARS:
        print(f"warning: INSTRUCTIONS.md is {len(text)} chars; Claude Code truncates context "
              f"beyond {CONTEXT_WARN_CHARS} and Codex budgets far less", file=sys.stderr)
    return text


def with_banner(data, source):
    """Prepend a do-not-edit banner. JSON has no comments, so it's a "//" key
    (the convention package.json uses); every harness ignores unknown keys in
    its manifest. Not used for hook payloads: those are parsed at runtime by
    four different harnesses, so they say "generated" in their filename instead."""
    banner = [
        "##################################################################",
        "#  GENERATED FILE - DO NOT EDIT HERE. Your changes will be lost. #",
        f"#  Edit instead: {source:<48}#",
        "#  CI regenerates this file automatically on every push.         #",
        "#  (Or run locally: python3 scripts/sync.py)                     #",
        "##################################################################",
    ]
    return {"//": banner, **data}


def hook_payloads(text):
    if not text:
        return {}, {}
    return (
        {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}},
        {"additionalContext": text},
    )


def build():
    plugin = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    validate(plugin)
    meta = {k: plugin[k] for k in META_KEYS if k in plugin}
    marketplace = {
        "name": f"{meta['name']}-marketplace",
        "owner": {"name": meta.get("author", {}).get("name", meta["name"])},
        "description": f"Marketplace for the {meta['name']} plugin.",
        "plugins": [{
            "name": meta["name"],
            "description": meta.get("description", ""),
            "version": meta.get("version", "0.0.0"),
            "source": "./",
        }],
    }
    gemini = {k: meta[k] for k in ("name", "version", "description") if k in meta}
    standard, copilot = hook_payloads(load_instructions())
    return {
        # path: (data, compact). Hook payloads are compact single-line ASCII JSON:
        # Copilot requires one line, and pure ASCII (\uXXXX escapes) survives any
        # console encoding, including Windows PowerShell 5.1's.
        ".claude-plugin/plugin.json": (with_banner(meta, "plugin.json (repo root)"), False),
        ".claude-plugin/marketplace.json": (with_banner(marketplace, "plugin.json (repo root)"), False),
        "gemini-extension.json": (with_banner(gemini, "plugin.json (repo root)"), False),
        "hooks/session-start.generated.json": (standard, True),
        "com.github.copilot/hooks/session-start.generated.json": (copilot, True),
    }


def render(data, compact):
    if compact:
        return json.dumps(data, separators=(",", ":"), ensure_ascii=True) + "\n"
    return json.dumps(data, indent=2) + "\n"


def main():
    check = "--check" in sys.argv
    try:
        outputs = build()
    except (SyncError, json.JSONDecodeError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    stale = []
    for rel, (data, compact) in outputs.items():
        path = ROOT / rel
        text = render(data, compact)
        if path.exists() and path.read_text(encoding="utf-8") == text:
            continue
        if check:
            stale.append(rel)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")
            print(f"wrote {rel}")
    if stale:
        print("stale generated files (run python3 scripts/sync.py):\n  " + "\n  ".join(stale), file=sys.stderr)
        return 1
    if check:
        print("all generated files up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
