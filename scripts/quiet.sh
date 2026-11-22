#!/usr/bin/env bash
# quiet.sh — run a command, keep its FULL output in a log file, print only a short summary.
#   quiet.sh NAME -- command [args...]
# Env: CC_LOG_DIR (default .claude/logs), CC_TAIL (default 15). Exit status = the command's exit status.
# Portable bash (Linux, macOS bash 3.2+, Git Bash / WSL on Windows).
set -uo pipefail
if [ $# -lt 3 ] || [ "$2" != "--" ]; then echo "usage: $0 NAME -- command [args...]" >&2; exit 2; fi
name=$1; shift 2
dir=${CC_LOG_DIR:-.claude/logs}
mkdir -p "$dir" || exit 2
safe=$(printf '%s' "$name" | tr -c 'A-Za-z0-9_.-' '_')
log="$dir/$(date -u +%Y%m%dT%H%M%SZ)-$safe.log"
t0=$(date +%s)
"$@" >"$log" 2>&1
rc=$?
dt=$(( $(date +%s) - t0 ))
echo "[$name] exit=$rc duration=${dt}s lines=$(wc -l <"$log" | tr -d ' ') log=$log"
sum=$(grep -aE '([0-9]+ (passed|failed|errors?|skipped)|^Ran [0-9]+ tests?|^OK|^FAILED|Tests +[0-9]|Test Files +[0-9]|built in|error TS[0-9]+)' "$log" | tail -n 8)
if [ -n "$sum" ]; then echo "-- summary"; echo "$sum"; fi
if [ "$rc" -ne 0 ]; then
  first=$(grep -anE '(Traceback|^E   |AssertionError|Error:|error:|FAILED|×)' "$log" | head -n 1 | cut -d: -f1)
  if [ -n "$first" ]; then echo "-- first error (line $first)"; sed -n "${first},$((first + 14))p" "$log"; fi
fi
echo "-- tail"
tail -n "${CC_TAIL:-15}" "$log"
exit "$rc"
