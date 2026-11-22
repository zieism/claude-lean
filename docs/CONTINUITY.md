# Continuity: project memory + task checkpoints

Long sessions grow their context. Every call re-sends that context, so resetting between independent stages (a new
session or `/clear`) keeps calls small. Resetting is only safe if the essential state survives, hence two layers.

| Layer | File | Holds | Changes |
|---|---|---|---|
| Project memory | `.claude/checkpoints/PROJECT_MEMORY.md` | architecture, decisions and rationale, constraints, rejected approaches, evidence references, persistent knowledge | rarely, when a decision is made |
| Task checkpoint | `.claude/checkpoints/<TASK-ID>.md` (+ `ACTIVE`) | objective, current stage, completed work, files changed, tests performed, failures and retries, decision rationale, next action | at every stage end |

**Resume protocol:** read `ACTIVE` → that checkpoint → `PROJECT_MEMORY.md` → `CLAUDE.md` → do **Next action**.

**Limits:** a checkpoint restores what was written down, not the whole previous conversation. Nuances, abandoned
ideas or partially read files are lost unless recorded. Write decisions, failure signatures and the next action
before ending a session. The model cannot run `/clear` itself; you decide when to reset.
