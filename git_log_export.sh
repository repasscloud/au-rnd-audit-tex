#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./git_log_export.sh /path/to/repo /output/file.txt 2025-07-01 2026-06-30
# Example:
#   ./git_log_export.sh ~/src/myrepo evidence/git/repo-main.txt 2025-07-01 2026-06-30

REPO_PATH="${1:?repo path required}"
OUT_FILE="${2:?output file required}"
SINCE="${3:?since date required}"
UNTIL="${4:?until date required}"

mkdir -p "$(dirname "$OUT_FILE")"

git -C "$REPO_PATH" log \
  --since="$SINCE" \
  --until="$UNTIL" \
  --date=short \
  --pretty=format:'%h | %ad | %an | %d | %s' > "$OUT_FILE"

echo "Exported git log to: $OUT_FILE"
