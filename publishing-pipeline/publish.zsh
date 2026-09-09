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
stage_dir="$(mktemp -d "$pipeline_dir/.publish-stage.XXXXXX")"
stage_generated="$stage_dir/generated"
stage_output="$stage_dir/output"
trap 'rm -rf "$stage_dir"' EXIT

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
  --generated "$stage_generated"

tex_files=("$stage_generated"/*.tex)
if (( ${#tex_files[@]} != 7 )); then
  echo "Expected 7 generated TeX documents, found ${#tex_files[@]}." >&2
  exit 1
fi

mkdir -p "$stage_output"
for tex_file in "${tex_files[@]}"; do
  echo "Compiling ${tex_file:t}"
  build_log="$(mktemp)"
  if ! tectonic --outdir "$stage_output" "$tex_file" >"$build_log" 2>&1; then
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

cp "$generated_dir/.gitkeep" "$stage_generated/.gitkeep"
cp "$output_dir/.gitkeep" "$stage_output/.gitkeep"
backup_generated="$stage_dir/generated.previous"
backup_output="$stage_dir/output.previous"
mv "$generated_dir" "$backup_generated"
mv "$output_dir" "$backup_output"
if ! mv "$stage_generated" "$generated_dir"; then
  mv "$backup_generated" "$generated_dir"
  mv "$backup_output" "$output_dir"
  exit 1
fi
if ! mv "$stage_output" "$output_dir"; then
  rm -rf "$generated_dir"
  mv "$backup_generated" "$generated_dir"
  mv "$backup_output" "$output_dir"
  exit 1
fi
rm -rf "$backup_generated" "$backup_output"

echo "Published 7 PDFs to $output_dir with no warnings."
