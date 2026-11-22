# Usage

## Invoke the skill
The skill loads automatically when Claude Code judges a task multi-step. You can also ask for it explicitly:
> Use the token-efficient-workflow skill for this task: <task>.

or type `/token-efficient-workflow` if your Claude Code version exposes skills as slash commands.

## Example workflow
1. **Start:** “Use token-efficient-workflow. Task T-12: add rate limiting to the upload endpoint.”
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
The skill uses whatever model you selected and never switches models. If it believes another model is warranted,
it says so once and leaves the decision to you.
