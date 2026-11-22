# Security policy

## What this toolkit touches
- Writes only: `<claude dir>/skills/token-efficient-workflow/SKILL.md`, `<claude dir>/budget-manager/*`, and (with
  `--project`) `<project>/.claude/checkpoints/*` and one `.gitignore` line. `<claude dir>` is `$CLAUDE_CONFIG_DIR` or
  `~/.claude`.
- Never reads or writes credentials, Claude settings files, model or effort selection, model environment variables,
  billing, or network resources.
- `usage_report.py` reads transcripts **read-only** and prints aggregates only (no prompts, replies, tool inputs or
  outputs).

## Privacy guidance
- Checkpoints, project memory and `.claude/logs/` may contain project details. Review them before committing to a
  public repository; keep `.claude/logs/` ignored (the installer adds it to `.gitignore`).
- Never paste raw transcripts into issues. Share `usage_report.py --json --hide-project` output instead.

## Reporting a vulnerability
Please use GitHub's private vulnerability reporting ("Security" tab → "Report a vulnerability") instead of a public
issue. Include the version, operating system and steps to reproduce. We aim to acknowledge within 7 days.
