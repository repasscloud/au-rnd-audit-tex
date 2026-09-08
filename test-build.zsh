#!/usr/bin/env zsh

set -eu
setopt pipe_fail null_glob

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "test-build.zsh only runs on macOS. On Linux, run ./test-build.sh." >&2
  exit 1
fi

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
