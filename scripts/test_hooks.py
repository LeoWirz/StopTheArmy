#!/usr/bin/env python3
"""Run every session-start hook command exactly as each harness would.

Reads the commands straight from the hook files, then executes them in every
shell found on this machine: sh/bash/dash (Linux, macOS), Git Bash (Windows),
PowerShell 7 (pwsh) and Windows PowerShell 5.1. Shells that aren't installed
are skipped and reported. CI runs this on Linux, macOS and Windows.

The fake plugin root contains a space, and the instructions contain non-ASCII
text and quotes, because those are what usually break on Windows.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import sync  # noqa: E402

TEXT = 'Réponds en français. Use "double" and \'single\' quotes, a back\\slash, & 100% $HOME.'
WINDOWS = os.name == "nt"
PLUGIN_VARS = ("PLUGIN_ROOT", "CLAUDE_PLUGIN_ROOT", "COPILOT_PLUGIN_ROOT", "extensionPath")


def posix_shells():
    if WINDOWS:
        git_bash = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Git" / "bin" / "bash.exe"
        return [("git-bash", [str(git_bash), "-c"])] if git_bash.exists() else []
    return [(n, [shutil.which(n), "-c"]) for n in ("sh", "bash", "dash") if shutil.which(n)]


def powershells():
    found = []
    for name in ("pwsh", "powershell"):
        exe = shutil.which(name)
        if exe:
            found.append((name, [exe, "-NoProfile", "-NonInteractive", "-Command"]))
    return found


def run(argv, command, env_vars):
    env = {k: v for k, v in os.environ.items() if k not in PLUGIN_VARS}
    env.update(env_vars)
    proc = subprocess.run(argv + [command], capture_output=True, text=True, encoding="utf-8",
                          timeout=60, env=env, cwd=tempfile.gettempdir())
    return proc


def main():
    assert sync.hook_payloads("") == ({}, {}), "empty instructions must inject nothing"
    standard, copilot = sync.hook_payloads(TEXT)

    hooks = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    shared = hooks["hooks"]["SessionStart"][0]["hooks"][0]
    cop_hooks = json.loads((ROOT / "com.github.copilot" / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    cop = cop_hooks["hooks"]["sessionStart"][0]

    failures, passed, skipped = [], 0, []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "plugin root"
        for rel, data in (("hooks/session-start.generated.json", standard),
                          ("com.github.copilot/hooks/session-start.generated.json", copilot)):
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text(sync.render(data, compact=True), encoding="utf-8", newline="\n")
        r = str(root)
        gemini_cmd = shared["command"].replace("${extensionPath}", r)  # Gemini substitutes textually

        cases = []  # (label, shell argv, command, env vars, expected output)
        sh, ps = posix_shells(), powershells()
        if not sh:
            skipped.append("POSIX shell / Git Bash")
        if not ps:
            skipped.append("PowerShell")
        for name, argv in sh:
            cases += [
                (f"Claude Code [{name}]", argv, shared["command"], {"CLAUDE_PLUGIN_ROOT": r}, standard),
                (f"Codex [{name}]", argv, shared["command"], {"PLUGIN_ROOT": r, "CLAUDE_PLUGIN_ROOT": r}, standard),
                (f"Copilot [{name}]", argv, cop["bash"], {"PLUGIN_ROOT": r, "CLAUDE_PLUGIN_ROOT": r}, copilot),
            ]
            if not WINDOWS:  # Gemini uses bash on Unix, PowerShell on Windows
                cases.append((f"Gemini [{name}]", argv, gemini_cmd, {}, standard))
        # PowerShell parses the WHOLE shared command before running any of it, so
        # line 1 (the sh part) must be valid PowerShell syntax too. Parse-check
        # it on every OS, including after Gemini substitutes a Windows path.
        win_ext = r"C:\Users\Jane Doe\.gemini\extensions\stop-the-army"
        parse_only = ("$e = $null; [void][System.Management.Automation.Language.Parser]::ParseInput("
                      "$env:HOOK_CMD, [ref]$null, [ref]$e); "
                      "if ($e) { $e | ForEach-Object { $_.Message }; exit 1 }; '{}'")
        for name, argv in ps:
            for label, cmd in (("shared command", shared["command"]),
                               ("shared command, Gemini Windows path", shared["command"].replace("${extensionPath}", win_ext))):
                cases.append((f"parses in PowerShell: {label} [{name}]", argv, parse_only, {"HOOK_CMD": cmd}, {}))
            cases += [
                (f"Codex commandWindows [{name}]", argv, shared["commandWindows"],
                 {"PLUGIN_ROOT": r, "CLAUDE_PLUGIN_ROOT": r}, standard),
                (f"Copilot [{name}]", argv, cop["powershell"], {"PLUGIN_ROOT": r, "CLAUDE_PLUGIN_ROOT": r}, copilot),
            ]
            # Only Windows runs the shared command in PowerShell (Claude Code without
            # Git Bash; Gemini). Elsewhere they use sh/bash, and PowerShell 7 on
            # Linux/macOS even has an `exec` alias, which would change line 1.
            if WINDOWS:
                cases += [
                    (f"Claude Code [{name}]", argv, shared["command"], {"CLAUDE_PLUGIN_ROOT": r}, standard),
                    # Gemini appends this exit-code check to every Windows hook command
                    (f"Gemini [{name}]", argv, gemini_cmd + "; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }", {}, standard),
                ]

        for label, argv, command, env_vars, expected in cases:
            proc = run(argv, command, env_vars)
            try:
                ok = proc.returncode == 0 and json.loads(proc.stdout) == expected
            except json.JSONDecodeError:
                ok = False
            if ok:
                passed += 1
                print(f"  ok    {label}")
            else:
                failures.append(label)
                print(f"  FAIL  {label}: exit={proc.returncode}\n        stdout={proc.stdout!r}\n        stderr={proc.stderr.strip()!r}")

    if skipped:
        print(f"skipped (not installed here): {', '.join(skipped)}")
    if failures:
        print(f"{len(failures)} hook case(s) failed", file=sys.stderr)
        return 1
    print(f"all {passed} hook cases passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
