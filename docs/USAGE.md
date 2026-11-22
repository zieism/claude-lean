# Usage

## Invoke the skill
The skill loads automatically when Claude Code judges a task multi-step. You can also ask for it explicitly:
> /claude-lean <task>

or in plain words: “Use the claude-lean skill for this task: <task>.”

`/token-efficient-workflow` still works in v0.1.x as a deprecated alias that loads `claude-lean`.

## Example workflow
1. **Start:** `/claude-lean Task T-12: add rate limiting to the upload endpoint.`
2. **Checkpoint:** Claude creates `.claude/checkpoints/T-12.md` from the template, writes `T-12` into `ACTIVE`,
   and lists stages, each with an acceptance command. For example:

   | # | Stage | Acceptance |
   |---|---|---|
   | 1 | Limiter module | `pytest tests/test_limiter.py` → all pass |
   | 2 | Wire into endpoint | `pytest tests/test_upload.py -k limit` → pass |
   | 3 | Full validation | `pytest` → all pass |

3. **Per stage:**
   - plan, then batch the edits;
   - run the focused test through the quiet wrapper:
     `~/.claude/budget-manager/quiet.sh limiter -- pytest -q tests/test_limiter.py`;
   - run the broad suite once;
   - commit;
   - update the checkpoint.
4. **Failures:** after two identical failures, Claude records the signature and asks you instead of looping.
5. **Stage end:** Claude says whether a fresh session (or `/clear`) would materially shrink the context. If you
   start one, say “resume the active task”: it reads `ACTIVE`, the checkpoint and `PROJECT_MEMORY.md` and continues.

## Quiet wrapper
```bash
quiet.sh NAME -- <command> [args...]
# [NAME] exit=0 duration=12s lines=1840 log=.claude/logs/20260101T101500Z-NAME.log
# -- summary   (test counts, build result)
# -- first error (on failure)
# -- tail      (last 15 lines; CC_TAIL to change)
```
The exit status is the command's own. Logs go to `CC_LOG_DIR` (default `.claude/logs/`).

## Model selection
Claude Lean works with whatever model and effort settings you selected. It never edits the `model` field, never
runs `/model`, never sets model environment variables or CLI arguments, never switches models automatically, and
never recommends a model change to reduce token usage.
