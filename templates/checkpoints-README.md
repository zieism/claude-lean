# Task checkpoints
- `PROJECT_MEMORY.md` — durable project knowledge (architecture, decisions, constraints, rejected approaches).
- `<TASK-ID>.md` — one file per task, created from `TEMPLATE.md`.
- `ACTIVE` — one line with the task id currently in progress (empty = none).

Resuming in a fresh session: read `ACTIVE` → that checkpoint → `PROJECT_MEMORY.md` → `CLAUDE.md`, then do
**Next action**. A checkpoint restores the essential state of a task; it cannot reproduce every detail of the
previous conversation, so record anything that matters in it before the session ends.

Full command logs go to `.claude/logs/` (keep it out of version control).
