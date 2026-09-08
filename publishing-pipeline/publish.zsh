#!/usr/bin/env zsh

set -eu
setopt pipe_fail null_glob

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "publish.zsh only runs on macOS. On Linux, run ./publish.sh." >&2
  exit 1
fi

pipeline_dir="$(cd "$(dirname "$0")" && pwd)"
generated_dir="$pipeline_dir/generated"
output_dir="$pipeline_dir/output"
venv_dir="$pipeline_dir/.venv"

command -v python3 >/dev/null || { echo "python3 is required." >&2; exit 1; }
command -v tectonic >/dev/null || { echo "tectonic is required." >&2; exit 1; }

if [[ ! -x "$venv_dir/bin/python" ]]; then
  python3 -m venv "$venv_dir"
fi
"$venv_dir/bin/python" -m pip install --disable-pip-version-check --quiet -r "$pipeline_dir/requirements.txt"
"$venv_dir/bin/python" -m unittest discover -s "$pipeline_dir/tests" -v
"$venv_dir/bin/python" "$pipeline_dir/scripts/publisher.py" \
  --input "$pipeline_dir/input" \
  --templates "$pipeline_dir/templates" \
  --generated "$generated_dir"

tex_files=("$generated_dir"/*.tex)
if (( ${#tex_files[@]} != 7 )); then
  echo "Expected 7 generated TeX documents, found ${#tex_files[@]}." >&2
  exit 1
fi

mkdir -p "$output_dir"
for tex_file in "${tex_files[@]}"; do
  echo "Compiling ${tex_file:t}"
  build_log="$(mktemp)"
  if ! tectonic --outdir "$output_dir" "$tex_file" >"$build_log" 2>&1; then
    cat "$build_log" >&2
    rm -f "$build_log"
    exit 1
  fi
  if grep -Eqi '^[[:space:]]*(warning|error):' "$build_log"; then
    cat "$build_log" >&2
    echo "Build failed because Tectonic emitted a warning or error: $tex_file" >&2
    rm -f "$build_log"
    exit 1
  fi
  rm -f "$build_log"
done

echo "Published 7 PDFs to $output_dir with no warnings."
