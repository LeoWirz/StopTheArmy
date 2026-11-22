---
name: write-documentation
description: Write or update documentation (README, guides, docstrings, API docs). Use when the user asks to document code, a feature, or a project, or after finishing an implementation, to offer a docs update.
allowed-tools: Read, Grep, Glob
---

After an implementation, offer the docs update in one line and wait for a yes before writing.

The reader is a human developer working on or with the project. Write for what they need to act.

First survey the project's existing documentation on the topic. Then place the content where a reader would look first: extend an existing file when one fits, otherwise create a new file and link it from the nearest index.

Keep a single source of truth: each fact lives in one place, everywhere else links to it. When the survey shows a fact duplicated, propose a reorganisation that consolidates it, and move content only after the user approves.

Document the present: state how things work now, as if they had always worked that way. When behaviour changes, rewrite the affected text in place so it describes the new behaviour. The story of what changed belongs in the commit message or changelog.

When the survey turns up stale text, fix it if it is part of the topic you are documenting; otherwise list it for the user at the end.

Write terse: the fewest words that let the reader act. Prefer a command, snippet, or example over a paragraph. When the details already live in the code, a config file, or `--help` output, point to that source instead of copying them, so the docs stay correct when the details change.

Done when every changed behaviour is documented in one place, in the present, every other mention links to it, and any stale text found is fixed or listed.
