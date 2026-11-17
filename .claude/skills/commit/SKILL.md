---
name: commit
description: Prepare and run a commit that follows writer_commits.md. Commits only the files the maintainer names (or has already staged).
argument-hint: '[what to include, e.g. "only the settings file"]'
disable-model-invocation: true
allowed-tools:
  - Bash(git add:*)
  - Bash(git commit:*)
---

# Commit

Maintainer's hint: $ARGUMENTS

## Steps

0. **Repository check:** if `git rev-parse --is-inside-work-tree` fails, stop. Give the maintainer `git init -b main` to run, then wait.
1. **Read the state:** `git status --short`, `git diff --staged`, `git diff` and `git branch --show-current`.
2. **Branch check:** never commit on `main`, except the repository's first commit. If the current branch is `main`, propose a branch name (see **Branches** in `writer_commits.md`), wait for confirmation, then `git switch -c <name>`.
3. **Choose what to commit**, in this order:
   - **Hint given:** only the files the hint describes. If something is already staged that the hint does not cover, list it and ask before unstaging it.
   - **No hint, something staged:** exactly the staged files.
   - **No hint, nothing staged:** group the changed and untracked files into logical changes (one type and scope each). One group: commit it. Several groups: list them and ask which to commit now.
4. **Part of a file:** if one file holds changes for two different commits, stop. Ask the maintainer to stage the wanted part with `git add -p <file>`, then run `/commit` again.
5. **Safety check:** never stage `.env` files, `node_modules/` or `.claude/settings.local.json`. If one is in the selection, stop and say so.
6. **Write the subject line** from the diff, following `writer_commits.md`.
7. **Show, then run:** show the `git add <path> ...` and `git commit -m "<subject>"` commands in one code block, then run them. Each one asks for the maintainer's approval; if the maintainer declines, stop.
8. **Report:** the commit hash and subject, and the files still uncommitted (from `git status --short`).
