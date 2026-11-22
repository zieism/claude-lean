# Measuring usage

`usage_report.py` reads local Claude Code transcripts (`~/.claude/projects/*/*.jsonl`, plus subagent files) and
prints **aggregates only**. It never prints prompts, replies, tool inputs or outputs.

```bash
usage_report.py                                    # all sessions
usage_report.py --session 1a2b3c --hide-project     # one session, without project names
usage_report.py --since 2026-01-01T09:00 --until 2026-01-01T12:00
usage_report.py --session 1a2b3c --stage s1=2026-01-01T09:00..2026-01-01T10:10 --stage s2=2026-01-01T10:10..2026-01-01T11:00
usage_report.py --json > usage.json                 # or --csv usage.csv
```

| Field | Meaning |
|---|---|
| `assistant_messages` | model responses (one per API call) |
| `input_tokens` / `output_tokens` | uncached input / generated output |
| `thinking_tokens` | reasoning share of output, when recorded |
| `cache_creation_input_tokens` / `cache_read_input_tokens` | cache writes / reads (the re-sent conversation context) |
| `cache_read_per_message` | average context re-read per call: the best single indicator of context growth |
| `tool_calls`, `tools`, `tool_errors` | tool use and failed tool results |
| `compactions` | automatic context compaction events |
| `duration_min` | first-to-last timestamp in the window |

**Correctness note:** Claude Code writes one transcript line per content block of a response (thinking, text, tool
call…), and each line repeats the response's usage. Summing every line over-counts tokens by the number of blocks.
The report counts usage once per (message id, request id) and tool calls once per tool-use id. Unknown record
shapes stop the report (exit 3) instead of being guessed.

## Tokens are not your subscription limit
These numbers describe model work recorded locally. Subscription usage limits are shown only by Claude Code
(`/usage`) or your account usage page, and how tokens map onto those limits is not published. This toolkit
cannot increase any limit.

## Comparing workflows fairly
1. Choose comparable tasks (similar size and type). Never compare a short validation run with a full development
   session.
2. For each task, record `/usage` before and after, the stage windows (UTC), stages completed and tests passed.
3. Run the report per stage window and compare `cache_read_per_message`, output and thinking tokens, tool calls,
   tool errors, compactions and duration.
4. Report absolute numbers and sample size. Savings are workload-dependent and not guaranteed.
