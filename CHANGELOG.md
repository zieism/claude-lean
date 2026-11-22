# Changelog

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
