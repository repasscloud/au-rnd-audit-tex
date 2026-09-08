#!/usr/bin/env bash

set -euo pipefail

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "test-build.sh only runs on Linux. On macOS, run ./test-build.zsh." >&2
  exit 1
fi

shopt -s nullglob

tex_files=(./*.tex)
if (( ${#tex_files[@]} == 0 )); then
  echo "No .tex files found." >&2
  exit 1
fi

for f in "${tex_files[@]}"; do
  echo "Compiling $f"
  build_log="$(mktemp)"
  if ! tectonic "$f" >"$build_log" 2>&1; then
    cat "$build_log" >&2
    rm -f "$build_log"
    exit 1
  fi
  if grep -Eqi '^[[:space:]]*(warning|error):' "$build_log"; then
    cat "$build_log" >&2
    echo "Build failed because Tectonic emitted a warning or error: $f" >&2
    rm -f "$build_log"
    exit 1
  fi
  rm -f "$build_log"
done

echo "All TeX documents compiled successfully with no warnings."
