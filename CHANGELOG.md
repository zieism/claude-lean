# Changelog

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
