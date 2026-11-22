---
name: review-changes
description: Review a branch or the current changes against the default branch, like a pull request review. Use when the user asks to review a branch, a PR, or their changes.
allowed-tools: Bash(git fetch *)
---

Review the changes a branch introduces relative to the default branch, as a pull request would show them. Without a branch, review the current work, including uncommitted and untracked files, against the default branch.

Fetch first so both sides reflect the remote's latest state. The review is read-only: branches and the working tree stay as they are. If a local branch and its remote have diverged, ask which one to review.

Report findings ranked by severity, each with its location and a suggested fix.
