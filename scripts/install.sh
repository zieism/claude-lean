#!/usr/bin/env bash
# install.sh — install Claude Lean (idempotent, non-destructive).
#   scripts/install.sh [--dry-run] [--force] [--project DIR] [--no-tools] [--no-alias]
# Installs:
#   <claude dir>/skills/claude-lean/SKILL.md                  (the skill: /claude-lean)
#   <claude dir>/skills/token-efficient-workflow/SKILL.md     (deprecated compatibility skill; skip with --no-alias)
#   <claude dir>/budget-manager/{quiet.sh,usage_report.py}   (helper tools; legacy folder name kept for upgrades) + MANIFEST
#   with --project DIR: DIR/.claude/checkpoints/{TEMPLATE.md,README.md,PROJECT_MEMORY.md,ACTIVE} (only if absent)
# <claude dir> = $CLAUDE_CONFIG_DIR if set, else ~/.claude.
# Never touches settings.json / settings.local.json, the selected model or effort settings, model environment
# variables, credentials, or anything outside the paths above.
# A file that differs from what this installer last wrote (your edits) is NOT overwritten without --force;
# with --force it is backed up first (<file>.bak-<UTC timestamp>).
set -euo pipefail
SRC=$(cd "$(dirname "$0")/.." && pwd)
CLAUDE_DIR=${CLAUDE_CONFIG_DIR:-$HOME/.claude}
DRY=0; FORCE=0; PROJECT=""; TOOLS=1; ALIAS=1
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY=1 ;; --force) FORCE=1 ;; --no-tools) TOOLS=0 ;; --no-alias) ALIAS=0 ;;
    --project) PROJECT=${2:?--project needs a directory}; shift ;;
    -h|--help) sed -n '2,14p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac; shift
done
hash() { if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | cut -d' ' -f1
         elif command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | cut -d' ' -f1
         else python3 -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$1"; fi; }
run() { if [ "$DRY" = 1 ]; then echo "  (dry-run) $*"; else "$@"; fi; }
MAN="$CLAUDE_DIR/budget-manager/MANIFEST"
recorded() { if [ -f "$MAN" ]; then awk -v p="$1" '$2==p{print $1}' "$MAN" | tail -n 1; fi; }
NEW_MAN=""; CONFLICT=0
place() {  # place SRC_FILE DEST_FILE MODE
  local s=$1 d=$2 mode=$3 hs hd rec
  hs=$(hash "$s")
  if [ ! -e "$d" ]; then echo "install   $d"; run mkdir -p "$(dirname "$d")"; run cp "$s" "$d"; run chmod "$mode" "$d"
  else
    hd=$(hash "$d"); rec=$(recorded "$d")
    if [ "$hd" = "$hs" ]; then echo "unchanged $d"
    elif [ -n "$rec" ] && [ "$rec" = "$hd" ]; then echo "upgrade   $d"; run cp "$s" "$d"; run chmod "$mode" "$d"
    elif [ "$FORCE" = 1 ]; then b="$d.bak-$(date -u +%Y%m%dT%H%M%SZ)"; echo "replace   $d (backup: $b)"; run cp -p "$d" "$b"; run cp "$s" "$d"; run chmod "$mode" "$d"
    else echo "KEEP      $d — modified or not installed by this toolkit; re-run with --force to replace (a backup is kept)"; CONFLICT=1; return 0; fi
  fi
  NEW_MAN="$NEW_MAN$hs $d
"
}
echo "Claude Lean v$(cat "$SRC/VERSION" 2>/dev/null || echo dev) — installing into $CLAUDE_DIR"
place "$SRC/skills/claude-lean/SKILL.md" "$CLAUDE_DIR/skills/claude-lean/SKILL.md" 644
# v0.1.0/v0.1.1 installed the full skill under the old name. An unmodified copy is upgraded to the alias stub;
# a customized copy is KEPT unchanged (never deleted or overwritten without --force).
[ "$ALIAS" = 1 ] && place "$SRC/skills/token-efficient-workflow/SKILL.md" "$CLAUDE_DIR/skills/token-efficient-workflow/SKILL.md" 644
if [ "$TOOLS" = 1 ]; then
  place "$SRC/scripts/quiet.sh" "$CLAUDE_DIR/budget-manager/quiet.sh" 755
  place "$SRC/scripts/usage_report.py" "$CLAUDE_DIR/budget-manager/usage_report.py" 755
fi
if [ "$DRY" = 0 ] && [ -n "$NEW_MAN" ]; then
  mkdir -p "$(dirname "$MAN")"
  { [ -f "$MAN" ] && awk 'NF==2' "$MAN"; printf '%s' "$NEW_MAN"; } | awk '{last[$2]=$1} END{for (p in last) print last[p], p}' | sort -k2 > "$MAN.tmp"
  mv "$MAN.tmp" "$MAN"
fi
if [ -n "$PROJECT" ]; then
  CK="$PROJECT/.claude/checkpoints"
  echo "Project checkpoints in $CK (existing files are never overwritten)"
  for pair in "templates/checkpoint.md:TEMPLATE.md" "templates/checkpoints-README.md:README.md" "templates/project-memory.md:PROJECT_MEMORY.md"; do
    s="$SRC/${pair%%:*}"; d="$CK/${pair##*:}"
    if [ -e "$d" ]; then echo "exists    $d"; else echo "create    $d"; run mkdir -p "$CK"; run cp "$s" "$d"; fi
  done
  if [ ! -e "$CK/ACTIVE" ]; then echo "create    $CK/ACTIVE"; run touch "$CK/ACTIVE"; fi
  if [ -d "$PROJECT/.git" ]; then
    if ! grep -qxF '.claude/logs/' "$PROJECT/.gitignore" 2>/dev/null; then echo "append    $PROJECT/.gitignore (.claude/logs/)"; [ "$DRY" = 1 ] || printf '\n.claude/logs/\n' >> "$PROJECT/.gitignore"; fi
  fi
fi
echo "Claude settings, your model and effort selection were not touched."
[ "$CONFLICT" = 1 ] && { echo "Some files were kept because they differ from this version (see KEEP above). /claude-lean is installed; a kept token-efficient-workflow skill keeps working as before."; exit 3; }
echo "Done. Start a new Claude Code session and use /claude-lean."
