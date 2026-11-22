#!/usr/bin/env sh
# Fallback for harnesses with no plugin system (Linux/macOS; on Windows use
# link-skills.ps1): symlink this plugin's skills into a skills directory the
# harness scans.
#   scripts/link-skills.sh                       # -> ./.agents/skills (current project)
#   scripts/link-skills.sh ~/.agents/skills      # user-wide
#   scripts/link-skills.sh .claude/skills        # any other skills dir
set -eu
root="$(cd "$(dirname "$0")/.." && pwd)"
dest="${1:-.agents/skills}"
mkdir -p "$dest"
for skill in "$root"/skills/*/; do
  name="$(basename "$skill")"
  ln -sfn "${skill%/}" "$dest/$name"
  echo "linked $dest/$name"
done
echo
echo "For always-on instructions, reference $root/INSTRUCTIONS.md from your"
echo "harness's global instructions file (e.g. ~/.codex/AGENTS.md)."
