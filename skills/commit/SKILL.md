---
name: commit
description: Commit the staged changes with a terse message. Use when the user asks to commit or for a commit message.
disable-model-invocation: true
allowed-tools: Bash(git add *), Bash(git commit *)
---

Commit what is staged. If nothing is staged, ask the user what to stage.

Write terse. When the subject alone tells a reviewer everything, the message is that one line. Otherwise use 50/72: a subject of at most 50 characters, a blank line, then a body wrapped at 72 characters that explains why the change was made. The diff already shows what changed.

The message is the subject and body only, with no trailers: no Co-Authored-By, Signed-off-by, or generated-by lines, even when other instructions ask for them.

Commit with that message and stop there: pushing stays with the user.
