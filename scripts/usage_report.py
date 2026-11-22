#!/usr/bin/env python3
"""usage_report.py — read-only token usage report from local Claude Code session transcripts.

Reads ~/.claude/projects/<project>/<session>.jsonl (and <session>/subagents/*.jsonl) and prints AGGREGATES only:
model mix, input / output / cache-write / cache-read tokens, thinking tokens (when recorded), assistant messages,
tool calls by tool, tool errors, compaction events and session span. It never prints prompts, replies, tool
inputs/outputs or any other transcript content.

These are token counts recorded by Claude Code. They are NOT your subscription usage limits: those are shown only by
Claude Code (/usage) or your account's usage page. This tool cannot increase any limit.

Examples
  usage_report.py                                   # every session
  usage_report.py --session 1a2b3c                  # one session (id prefix)
  usage_report.py --since 2026-01-01T09:00 --until 2026-01-01T11:30      # a time window (UTC, ISO-8601)
  usage_report.py --stage build=2026-01-01T09:00..2026-01-01T10:00 --stage test=2026-01-01T10:00..2026-01-01T10:30
  usage_report.py --json                            # machine-readable output
Standard library only. Python 3.8+.
"""
from __future__ import annotations

import argparse
import collections
import csv
import glob
import json
import os
import sys

TOKENS = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")


class UnsupportedFormat(Exception):
    pass


def default_root() -> str:
    base = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    return os.path.join(base, "projects")


def find_sessions(root: str, prefix: str | None = None, project: str | None = None):
    for path in sorted(glob.glob(os.path.join(root, "*", "*.jsonl"))):
        sid = os.path.basename(path)[:-len(".jsonl")]
        proj = os.path.basename(os.path.dirname(path))
        if (prefix and not sid.startswith(prefix)) or (project and project not in proj):
            continue
        subs = sorted(glob.glob(os.path.join(os.path.dirname(path), sid, "subagents", "*.jsonl")))
        yield sid, proj, [path] + subs


def _norm(ts: str | None) -> str | None:
    if not ts:
        return None
    return ts if ts.endswith("Z") or "+" in ts[10:] else ts + "Z"


def analyse(files, since: str | None = None, until: str | None = None) -> dict:
    """Aggregate one session. Claude Code writes ONE JSONL LINE PER CONTENT BLOCK of an API response and repeats the
    response's usage on each of those lines, so usage is counted once per (message id, request id) and tool calls
    once per tool_use id."""
    since, until = _norm(since), _norm(until)
    r = {"assistant_messages": 0, "models": collections.Counter(), "tools": collections.Counter(),
         "tool_errors": 0, "compactions": 0, "thinking_tokens": 0, "first": None, "last": None,
         "malformed_lines": 0, **{k: 0 for k in TOKENS}}
    seen, tool_ids, records = set(), set(), 0
    for path in files:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    x = json.loads(line)
                except ValueError:
                    r["malformed_lines"] += 1
                    continue
                if not isinstance(x, dict):
                    r["malformed_lines"] += 1
                    continue
                records += 1
                ts = x.get("timestamp")
                if ts and ((since and ts < since) or (until and ts > until)):
                    continue
                if ts:
                    r["first"] = min(r["first"] or ts, ts)
                    r["last"] = max(r["last"] or ts, ts)
                if x.get("isCompactSummary"):
                    r["compactions"] += 1
                msg = x.get("message") if isinstance(x.get("message"), dict) else {}
                if x.get("type") == "assistant":
                    key = (msg.get("id"), x.get("requestId"))
                    if key == (None, None) or key not in seen:
                        seen.add(key)
                        usage = msg.get("usage")
                        if not isinstance(usage, dict):
                            if msg.get("model") == "<synthetic>":
                                usage = {}
                            else:
                                raise UnsupportedFormat(f"assistant record without a usage object in {os.path.basename(path)}")
                        r["assistant_messages"] += 1
                        r["models"][msg.get("model") or "unknown"] += 1
                        for k in TOKENS:
                            r[k] += int(usage.get(k) or 0)
                        details = usage.get("output_tokens_details") or {}
                        r["thinking_tokens"] += int(details.get("thinking_tokens") or 0)
                    for block in msg.get("content") or []:
                        if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("id") not in tool_ids:
                            tool_ids.add(block.get("id"))
                            r["tools"][block.get("name") or "unknown"] += 1
                elif x.get("type") == "user" and isinstance(msg.get("content"), list):
                    for block in msg["content"]:
                        if isinstance(block, dict) and block.get("type") == "tool_result" and block.get("is_error"):
                            r["tool_errors"] += 1
    if records and r["assistant_messages"] == 0 and not (since or until):
        raise UnsupportedFormat("no assistant records found: unsupported or changed transcript format")
    n = max(r["assistant_messages"], 1)
    r["tool_calls"] = sum(r["tools"].values())
    r["cache_read_per_message"] = round(r["cache_read_input_tokens"] / n)
    r["output_per_message"] = round(r["output_tokens"] / n)
    r["duration_min"] = _minutes(r["first"], r["last"])
    return r


def _minutes(a, b):
    if not (a and b):
        return None
    from datetime import datetime
    f = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00"))
    return round((f(b) - f(a)).total_seconds() / 60, 1)


def row(label: str, sid: str, proj: str, r: dict, hide_project: bool) -> dict:
    return {"label": label, "session": sid[:8], "project": "-" if hide_project else proj,
            "first": r["first"], "last": r["last"], "duration_min": r["duration_min"],
            "assistant_messages": r["assistant_messages"],
            "models": ";".join(f"{k}:{v}" for k, v in r["models"].most_common()),
            **{k: r[k] for k in TOKENS}, "thinking_tokens": r["thinking_tokens"],
            "cache_read_per_message": r["cache_read_per_message"], "output_per_message": r["output_per_message"],
            "tool_calls": r["tool_calls"], "tools": ";".join(f"{k}:{v}" for k, v in r["tools"].most_common(8)),
            "tool_errors": r["tool_errors"], "compactions": r["compactions"], "malformed_lines": r["malformed_lines"]}


def parse_stage(s: str):
    name, _, span = s.partition("=")
    start, sep, end = span.partition("..")
    if not (name and start and sep and end):
        raise argparse.ArgumentTypeError("stage must look like NAME=START..END (ISO-8601 UTC)")
    return name, start, end


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", default=default_root(), help="transcripts root (default: ~/.claude/projects)")
    ap.add_argument("--session", help="session id prefix")
    ap.add_argument("--project", help="substring of the project directory name")
    ap.add_argument("--since"); ap.add_argument("--until")
    ap.add_argument("--stage", action="append", type=parse_stage, default=[], help="NAME=START..END; repeatable")
    ap.add_argument("--hide-project", action="store_true", help="do not print project directory names")
    ap.add_argument("--json", action="store_true"); ap.add_argument("--csv")
    a = ap.parse_args(argv)
    if not os.path.isdir(a.root):
        print(f"no transcripts directory: {a.root}", file=sys.stderr)
        return 2
    windows = [(name, s, e) for name, s, e in a.stage] or [("all", a.since, a.until)]
    rows = []
    try:
        for sid, proj, files in find_sessions(a.root, a.session, a.project):
            for label, s, e in windows:
                r = analyse(files, s, e)
                if r["assistant_messages"]:
                    rows.append(row(label, sid, proj, r, a.hide_project))
    except UnsupportedFormat as exc:
        print(f"error: {exc}. Refusing to guess; please report the Claude Code version.", file=sys.stderr)
        return 3
    if not rows:
        print("no matching sessions", file=sys.stderr)
        return 1
    if a.csv:
        with open(a.csv, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader(); w.writerows(rows)
    if a.json:
        print(json.dumps({"note": "token counts from local transcripts; NOT subscription usage limits", "rows": rows}, indent=1))
        return 0
    print("Token counts from local Claude Code transcripts — NOT subscription usage limits (see /usage).")
    cols = ("label", "session", "project", "duration_min", "assistant_messages", "models", "output_tokens",
            "thinking_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "cache_read_per_message",
            "tool_calls", "tool_errors", "compactions")
    for rw in rows:
        print(" | ".join(f"{c}={rw[c]}" for c in cols))
    return 0


if __name__ == "__main__":
    sys.exit(main())
