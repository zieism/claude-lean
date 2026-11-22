# Claude Lean

[![tests](https://github.com/zieism/claude-lean/actions/workflows/tests.yml/badge.svg)](https://github.com/zieism/claude-lean/actions/workflows/tests.yml)
[![release](https://img.shields.io/github/v/release/zieism/claude-lean)](https://github.com/zieism/claude-lean/releases/latest)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

_Formerly “Claude Code Budget Manager”. Invoke it with **`/claude-lean`**. `/token-efficient-workflow` remains only as a deprecated compatibility skill (see [Migration](#migrating-from-v010--v011))._

A lightweight, dependency-free toolkit for **reducing unnecessary token consumption in Claude Code** during
long-running development work, without lowering reasoning quality or test discipline.

It gives Claude a disciplined working style (a skill), gives you durable task state (checkpoints) so sessions can be
reset safely, keeps noisy command output out of the context, and lets you **measure** what a session actually used.

> **What Claude Lean is — and is not**
> - It optimizes **workflow efficiency** (context size, call count, output noise, retries), **not** subscription quotas.
> - It **never changes your selected model** or effort settings, and never recommends a model change to save tokens.
> - It does **not guarantee** token savings: effects depend on your workload.
> - It **cannot bypass** Claude usage limits.
> - It does **not reset sessions automatically**: it only recommends when a fresh session would help.
> - It does **not enable paid API billing** and makes no API calls.

## Commands at a glance
| Command | What it does |
|---|---|
| `/claude-lean <task>` | Run a task with the Claude Lean workflow (primary command) |
| `/token-efficient-workflow` | Deprecated compatibility skill (not a native alias): loads `claude-lean` |
| `~/.claude/budget-manager/quiet.sh NAME -- <cmd>` | Run a command with the full log on disk and a short summary in context |
| `~/.claude/budget-manager/usage_report.py --session <id>` | Read-only token report for a session (not subscription usage) |

The helper tools live in `~/.claude/budget-manager/`. That is their current location; only the directory name is legacy (see [Installation paths](#installation-paths)).

## What it does
- **`claude-lean` skill** (`/claude-lean`):
  - bounded stages with measurable acceptance criteria;
  - focused tests before broad suites;
  - quiet command output;
  - at most two attempts per identical failure;
  - no unnecessary subagents;
  - your selected model is preserved (never switched automatically);
  - explicit context-reset recommendations.
- **Two-layer continuity:**
  - **project memory**: architecture, decisions, constraints, rejected approaches;
  - **task checkpoints**: objective, stage, work done, files, tests, failures, next action;
  - a fresh session can resume from files instead of a long conversation.
- **`quiet.sh`:** runs a command, keeps the full log on disk, prints only exit status, test summary, first error and
  a short tail.
- **`usage_report.py`:** a read-only report of tokens, cache reads/writes, thinking tokens, tool calls, errors,
  compactions and duration, per session or per stage window, from local transcripts. It never prints transcript
  content.
- **Safe installer/uninstaller:** idempotent, keeps your edits, never touches `settings.json`.

## What it does not do
- It does not switch models, change settings, store credentials or call any API.
- It does not run background processes or orchestrate sessions automatically.
- It does not guarantee or estimate savings for you: you measure them.

## Architecture
```mermaid
flowchart LR
  U[You] -->|task| CC[Claude Code session<br/>your selected model]
  SK[skill: claude-lean] -. guides .-> CC
  CC -->|reads / updates| CP[(.claude/checkpoints/<br/>TASK checkpoint + ACTIVE)]
  CC -->|reads / updates decisions| PM[(PROJECT_MEMORY.md)]
  CC -->|runs commands via| Q[quiet.sh]
  Q -->|full output| L[(.claude/logs/*.log)]
  Q -->|short summary| CC
  CC -.->|writes| T[(~/.claude/projects/*.jsonl<br/>transcripts)]
  T -->|read-only| R[usage_report.py]
  R -->|aggregates only| U
  CP -->|resume in a fresh session| CC
```

## Requirements
- Claude Code (skills support).
- `bash` for the installer and `quiet.sh`: Linux and macOS; Git Bash or WSL on Windows.
- Python 3.8+ for `usage_report.py` (standard library only).

## Installation
Inspect before you run anything:
```bash
git clone --branch v0.1.3 https://github.com/zieism/claude-lean.git
cd claude-lean
less scripts/install.sh
scripts/install.sh --dry-run
scripts/install.sh
```
`--dry-run` shows every action and changes nothing; the last command installs the user-level skill and tools.

Optional, from the same `claude-lean` directory: add checkpoint templates to one of your projects:
```bash
scripts/install.sh --project ~/code/app
```
- Installs into `$CLAUDE_CONFIG_DIR` (if set) or `~/.claude`.
- Re-running is safe (`unchanged`).
- Files you edited are kept unless you pass `--force`, which keeps a backup.
- Manual and Windows instructions: [docs/INSTALLATION.md](docs/INSTALLATION.md).

## Installation paths
Current installation (v0.1.3). `~` means `$CLAUDE_CONFIG_DIR` if set, otherwise your home directory's `.claude`.

| Path | Status |
|---|---|
| `~/.claude/skills/claude-lean/SKILL.md` | **Current**: the primary skill, invoked as `/claude-lean` |
| `~/.claude/budget-manager/quiet.sh`, `usage_report.py`, `MANIFEST` | **Current location, legacy name**: the helper tools are still installed here. The directory keeps its pre-rename name so upgrades and uninstalls of earlier installs stay safe; it will only move in a future release with a tested migration |
| `~/.claude/skills/token-efficient-workflow/SKILL.md` | **Deprecated compatibility skill**: a short stub that loads `claude-lean` (skip it with `--no-alias`); this was the skill's location before v0.1.2 |
| `<project>/.claude/checkpoints/` | **Current**: project checkpoints (created with `--project`) |

Legacy names that are **not** current: the project name “Claude Code Budget Manager” and the repository URL
`github.com/zieism/claude-code-budget-manager`, which redirects to `github.com/zieism/claude-lean`.

## Quick start
1. Start a new Claude Code session in your project and say:
   > /claude-lean Task T-1: <your task>

   (or: “Use the claude-lean skill. Task T-1: …”)
2. Claude creates `.claude/checkpoints/T-1.md` with stages and acceptance criteria, then works stage by stage.
3. At a stage boundary it tells you whether a fresh session would materially reduce context. To resume later, say
   “resume the active task”.

See [docs/USAGE.md](docs/USAGE.md) for an end-to-end example.

## Measuring usage
```bash
~/.claude/budget-manager/usage_report.py --session <id-prefix> --hide-project
~/.claude/budget-manager/usage_report.py --session <id> --stage build=2026-01-01T09:00..2026-01-01T10:00 --json
```
- `cache_read_per_message` (context re-sent per call) is usually the clearest signal of context growth.
- The report handles Claude Code's one-line-per-content-block transcript layout (usage counted once per response).
- **Token counts are not subscription usage:** check `/usage` in Claude Code.
- How to compare workflows fairly: [docs/MEASUREMENT.md](docs/MEASUREMENT.md).

## Checkpoint recovery
Read `ACTIVE` → the task checkpoint → `PROJECT_MEMORY.md` → `CLAUDE.md`, then continue with **Next action**.
Checkpoints keep what was written down, not every detail of a conversation. See
[docs/CONTINUITY.md](docs/CONTINUITY.md).

## Security and privacy
- No network access, no credentials, no settings changes.
- The report prints aggregates only.
- Checkpoints and `.claude/logs/` may contain project details: review them before committing publicly (the
  installer adds `.claude/logs/` to `.gitignore`).
- Report vulnerabilities privately: [SECURITY.md](SECURITY.md).

## Troubleshooting
| Symptom | Fix |
|---|---|
| Skill not listed | Start a **new** session after installing; check `~/.claude/skills/claude-lean/SKILL.md` exists (or `$CLAUDE_CONFIG_DIR/...`). |
| Installer exits 3 with `KEEP` | A file differs from this version (your edits or another tool). Review it; use `--force` to replace it (a backup is kept). |
| Tools are under `~/.claude/budget-manager/` | Expected: this is the current tools location with its legacy name, kept so earlier installs upgrade and uninstall cleanly (see [Installation paths](#installation-paths)). |
| `usage_report.py` exits 3 | Your Claude Code transcript format is not recognised. Please open an issue with your Claude Code version (no transcript content). |
| `no matching sessions` | Check `--root`, `--session` prefix and the time window (UTC). |
| Windows | Use the manual skill copy and `py scripts\usage_report.py`; shell scripts need Git Bash or WSL. |

## Migrating from v0.1.0 / v0.1.1
The skill was named `token-efficient-workflow` before v0.1.2. Re-running `scripts/install.sh`:
- installs **`/claude-lean`** (the full skill);
- replaces an **unmodified** old `token-efficient-workflow` skill with a short **deprecated compatibility skill**
  that loads `claude-lean`, so `/token-efficient-workflow` keeps working;
- **keeps a customized** old skill untouched (reported as `KEEP`, exit code 3), next to `/claude-lean`. Merge your
  changes into `claude-lean` if you want them there, then use `--force` to replace the old file (a backup is kept).

The compatibility skill is a plain skill that tells Claude to load `claude-lean`; it is not a native Claude Code alias.
Skip it with `--no-alias`. It will be removed in a future minor release.

## Known limitations
See [docs/LIMITATIONS.md](docs/LIMITATIONS.md):
- no guaranteed savings;
- tokens ≠ plan limits;
- the transcript format may change;
- context resets are manual;
- Windows is untested.

## Uninstallation
```bash
scripts/uninstall.sh --dry-run && scripts/uninstall.sh
```
Removes only unmodified installed files. It never touches settings, your model or project checkpoints.

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md): standard library only, synthetic test data only, and no unmeasured savings
claims.

## License
[MIT](LICENSE). It is short and permissive, the norm for small developer tools, and lets anyone adapt the skill and
scripts to their own workflow with minimal friction.
