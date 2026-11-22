# Installation

Requirements: Claude Code, `bash` (Linux, macOS, or Git Bash / WSL on Windows), Python 3.8+ for the usage report.
No other dependencies.

## 1. Get the files and inspect them first
```bash
git clone --branch v0.1.2 https://github.com/zieism/claude-lean.git
cd claude-lean
less scripts/install.sh
scripts/install.sh --dry-run
scripts/install.sh
```
Read `install.sh` before running it; `--dry-run` shows every action and changes nothing.
The repository was renamed from `claude-code-budget-manager`; old URLs redirect. Prefer a pinned release: `git checkout v0.1.2` (or download the release archive and verify it before use).
Do not pipe remote scripts into a shell.

## 2. Install
```bash
scripts/install.sh                          # skill + helper tools (user level)
scripts/install.sh --project /path/to/repo  # also create .claude/checkpoints/ templates in a project
```
One-command form (still inspectable, pinned):
```bash
git clone --branch v0.1.2 https://github.com/zieism/claude-lean.git && claude-lean/scripts/install.sh --dry-run
```
Run it again without `--dry-run` after reviewing the plan.

What gets installed (`<claude dir>` = `$CLAUDE_CONFIG_DIR` or `~/.claude`):
| Path | Purpose |
|---|---|
| `<claude dir>/skills/claude-lean/SKILL.md` | the skill, `/claude-lean` (user level: all projects) |
| `<claude dir>/skills/token-efficient-workflow/SKILL.md` | deprecated compatibility skill (not a native alias) that loads `claude-lean` (skip with `--no-alias`; a customized old copy is kept) |
| `<claude dir>/budget-manager/quiet.sh`, `usage_report.py` | helper tools (current location; legacy directory name) |
| `<claude dir>/budget-manager/MANIFEST` | sha256 of installed files (for safe upgrades and removal) |
| `<project>/.claude/checkpoints/{TEMPLATE.md,README.md,PROJECT_MEMORY.md,ACTIVE}` | only with `--project`, only if absent |

Behaviour:
- **Idempotent:** re-running reports `unchanged`.
- **Upgrades** replace only files whose content still matches what the installer wrote.
- **Your edits are kept:** a modified or foreign file is reported as `KEEP` (exit code 3). `--force` replaces it
  after saving `<file>.bak-<timestamp>`.
- Claude settings files, your model and effort selection, model environment variables and billing are never touched.
- The helper tools are installed in `budget-manager/`: that is their **current** location; only the name predates
  the rename. Changing it needs a tested migration, so it stays in v0.1.x.

Start a new Claude Code session afterwards; check with `/skills` (or ask “which skills are available?”).

## Manual installation (any OS)
Copy `skills/claude-lean/SKILL.md` to `~/.claude/skills/claude-lean/SKILL.md`
(Windows: `%USERPROFILE%\.claude\skills\claude-lean\SKILL.md`). The deprecated compatibility skill in `skills/token-efficient-workflow/` is optional. Optionally copy `scripts/quiet.sh`,
`scripts/usage_report.py` anywhere on your PATH and `templates/` into `<project>/.claude/checkpoints/`
(`checkpoint.md` → `TEMPLATE.md`, `project-memory.md` → `PROJECT_MEMORY.md`, `checkpoints-README.md` → `README.md`).

## Windows
- **Skill:** manual copy as above (PowerShell):
  ```powershell
  New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\skills\claude-lean" | Out-Null
  Copy-Item skills\claude-lean\SKILL.md "$env:USERPROFILE\.claude\skills\claude-lean\SKILL.md"
  ```
- `usage_report.py`: `py scripts\usage_report.py` (standard library only).
- `install.sh` / `quiet.sh`: run under Git Bash or WSL.
- **Status:** Windows is **not yet tested** in CI. Reports are welcome.

## Uninstall
```bash
scripts/uninstall.sh --dry-run
scripts/uninstall.sh            # removes unmodified installed files; keeps edited ones (use --force to remove them)
```
Project checkpoints are your data and are never removed by the uninstaller.
