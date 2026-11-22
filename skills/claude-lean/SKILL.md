---
name: claude-lean
description: Use for multi-step or long-running software development work (implementation, debugging, refactoring, test fixing, audits). Works in bounded stages with measurable acceptance criteria and a project-local checkpoint, runs focused tests before broad suites, keeps command output out of the context, caps identical retries at two, avoids unnecessary subagents, never changes the user's selected model or effort settings, and recommends context resets between independent stages.
---

# Claude Lean — token-efficient workflow

Most token use in long sessions comes from **context size × number of model calls**: every tool call re-sends the
conversation so far. Keep contexts short, calls few and outputs small. Never trade away required tests, safety rules
or the project's own instructions — they always take precedence over this skill.

## 1. Start or resume
1. If `.claude/checkpoints/ACTIVE` exists and names a task, read **only** that checkpoint, the project memory file
   (`.claude/checkpoints/PROJECT_MEMORY.md`, if present) and the project's `CLAUDE.md`, then continue from the
   checkpoint's **Next action**. Do not re-explore what the checkpoint already records.
2. New task: copy `.claude/checkpoints/TEMPLATE.md` to `.claude/checkpoints/<TASK-ID>.md`, write the task id into
   `ACTIVE`, then fill in the objective and a stage list. Every stage needs a **measurable acceptance criterion**
   (a command and its expected result) and should fit one focused working session.
3. No checkpoint directory? Ask the user before creating one; otherwise keep the same structure in your replies.

## 2. Execute a stage
- Plan the whole change before touching files. Batch related edits, the focused test and the commit into as few
  tool calls as is safe. Avoid probe → fix → probe chains.
- Read only what you need (search first, then read the relevant range). Do not re-read unchanged files.
- Run long or noisy commands through a quiet wrapper (e.g. `quiet.sh NAME -- <command>`) so the full log stays on
  disk and only a summary enters the context. Without the wrapper, filter output (`tail`, `grep`) and save the full
  output to a log file.
- Do not paste large logs or JSON into replies; cite the log path and the decisive lines.
- Do not use subagents for implementation. Use one search subagent only when a genuinely broad search would
  otherwise pull many files into the main context. Never run parallel agents on the same task.
- Do not poll. Wait for completion notifications.

## 3. Tests
1. **Focused first**: the tests covering the change (a single test id or file).
2. **Broad once per stage**: the project's required wider suite before marking the stage done or committing.
   Never skip a required test and never weaken an assertion to make it pass.
3. Record the command, pass/fail counts and the log path in the checkpoint.

## 4. Failure budget
- A **failure signature** is the same failing command/test with the same error type and message.
- Make at most **two** fix attempts per identical signature. After the second identical failure, stop changing
  code, record the signature, both attempts and your best hypothesis under **Blockers**, and ask the user.
  A different signature starts a new count.

## 5. Model selection (strict: the user's choice is final)
- Work with the model and effort/thinking settings the user already selected. Claude Lean never changes them.
- Never edit the `model` field (or any effort or thinking setting) in Claude Code settings files.
- Never run `/model`, never set model-selection environment variables (such as `ANTHROPIC_MODEL`), and never pass
  model-selection command-line arguments.
- Never switch models automatically, and never recommend a model change to reduce token usage. Efficiency comes from
  short contexts, fewer calls, small outputs and bounded retries.
- Record the model in use per stage in the checkpoint's **Model log** (observe it; do not change it).
- Never enable or suggest paid API billing.

## 6. Finish a stage
1. Update the checkpoint: stage status, files changed, tests, failures, decisions, next action.
2. Move lasting knowledge (architecture, decisions and rationale, constraints, rejected approaches) into the project
   memory file — not task-level detail.
3. Commit according to the project's rules.
4. State in one line whether a fresh session (or `/clear`) would materially reduce context for the next stage. You
   cannot clear the context yourself; the user decides. A checkpoint restores essential state, not every detail.

## 7. Reporting
- Keep replies short: what changed, evidence (counts, paths), what is next.
- Token counts from transcripts are **estimates of model work**, not subscription usage. Usage limits are only what
  Claude Code (`/usage`) or the account usage page shows.
