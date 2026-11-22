#!/usr/bin/env bash
# uninstall.sh — remove what install.sh installed (non-destructive).
#   scripts/uninstall.sh [--dry-run] [--force]
# Removes only files listed in <claude dir>/budget-manager/MANIFEST whose content is unchanged since installation.
# Modified files are kept unless --force (then a backup <file>.bak-<UTC timestamp> is left in place).
# Never touches settings.json, the selected model, transcripts, or project checkpoints (.claude/checkpoints/ in your
# projects are your data — delete them yourself if you no longer want them).
set -euo pipefail
CLAUDE_DIR=${CLAUDE_CONFIG_DIR:-$HOME/.claude}
DRY=0; FORCE=0
while [ $# -gt 0 ]; do
  case "$1" in --dry-run) DRY=1 ;; --force) FORCE=1 ;; -h|--help) sed -n '2,8p' "$0"; exit 0 ;; *) echo "unknown option: $1" >&2; exit 2 ;; esac; shift
done
hash() { if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | cut -d' ' -f1
         elif command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | cut -d' ' -f1
         else python3 -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$1"; fi; }
run() { if [ "$DRY" = 1 ]; then echo "  (dry-run) $*"; else "$@"; fi; }
MAN="$CLAUDE_DIR/budget-manager/MANIFEST"
[ -f "$MAN" ] || { echo "Nothing to uninstall: no manifest at $MAN"; exit 0; }
KEPT=0
while read -r h p; do
  [ -n "${p:-}" ] || continue
  if [ ! -e "$p" ]; then echo "missing   $p"; continue; fi
  if [ "$(hash "$p")" = "$h" ]; then echo "remove    $p"; run rm -f "$p"
  elif [ "$FORCE" = 1 ]; then b="$p.bak-$(date -u +%Y%m%dT%H%M%SZ)"; echo "remove    $p (modified; backup: $b)"; run cp -p "$p" "$b"; run rm -f "$p"
  else echo "KEEP      $p — modified since installation; use --force to remove (a backup is kept)"; KEPT=1; fi
done < "$MAN"
if [ "$KEPT" = 0 ]; then
  echo "remove    $MAN"; run rm -f "$MAN"
  for d in "$CLAUDE_DIR/budget-manager" "$CLAUDE_DIR/skills/token-efficient-workflow"; do
    if [ -d "$d" ] && [ -z "$(ls -A "$d")" ]; then run rmdir "$d"; fi
  done
fi
echo "settings.json, your model selection and project checkpoints were not touched."
[ "$KEPT" = 1 ] && exit 3 || exit 0
