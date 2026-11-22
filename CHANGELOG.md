# Changelog

## v0.1.3 — documentation consistency release
- Installation docs now use the exact, verified sequence: `git clone --branch v0.1.3
  https://github.com/zieism/claude-lean.git`, `cd claude-lean`, `less scripts/install.sh`,
  `scripts/install.sh --dry-run`, `scripts/install.sh` (plus the optional `--project` example).
- The v0.1.2 tag's README still pointed to v0.1.1. This release makes the latest tag's README match `main`.
- Consistent naming: Claude Lean, `/claude-lean`; `/token-efficient-workflow` is described as a deprecated
  compatibility skill; a new "Installation paths" section separates current paths from legacy names.
- No changes to skill behaviour, installer logic or tests.

## v0.1.2
- The primary skill is now **`claude-lean`** (`/claude-lean`), matching the project name.
- `token-efficient-workflow` stays as a **deprecated alias** skill that loads `claude-lean`. It is a plain stub
  skill, not a built-in alias feature, and can be skipped with `--no-alias`.
- **Safe upgrade from v0.1.0 / v0.1.1:** an unmodified old skill is replaced by the alias; a **customized old skill
  is never overwritten or deleted** (reported `KEEP`) unless `--force`, which keeps a backup.
- Uninstall also removes `claude-lean` (manifest-based; customized files are kept).
- New tests: legacy upgrade (unmodified → alias), customized legacy skill preserved across install/uninstall,
  `--no-alias`.

## v0.1.1
- Renamed the project to **Claude Lean** (repository `zieism/claude-lean`; old URLs redirect). The skill name
  `token-efficient-workflow` and the tools folder `~/.claude/budget-manager/` are kept for compatibility.
- Strict model-preservation policy in the skill and docs: never edit `model` or effort settings, never run `/model`,
  never set model environment variables or CLI arguments, never switch models automatically, never recommend a
  model change to save tokens.
- New `TestModelPreservation` tests: the full install → re-install → project → force → quiet → report → uninstall
  lifecycle leaves settings files, model, effort and unrelated skills byte-identical; scripts contain no
  model-selection code.
- CI: Python 3.8 runs on `ubuntu-22.04` (ubuntu-latest no longer provides 3.8); Python 3.12 on Ubuntu and macOS.
- Clearer README statements on quotas, savings, usage limits, session resets and billing.

## v0.1.0 — initial release
- `token-efficient-workflow` skill: bounded stages with measurable acceptance criteria, project checkpoints,
  focused-then-broad testing, quiet command output, two-attempt failure budget, no unnecessary subagents,
  model selection preserved (never switched automatically), context-reset recommendations.
- Two-layer continuity templates: project memory + task checkpoint.
- `quiet.sh`: full command log on disk, short summary in context, exit status preserved.
- `usage_report.py`: read-only token report from local Claude Code transcripts (per session / per stage window),
  correct handling of usage repeated across content-block lines, no transcript content printed.
- Idempotent, non-destructive `install.sh` / `uninstall.sh` with a sha256 manifest; never touches `settings.json`.
- 15 stdlib unit tests; CI on Linux and macOS.
