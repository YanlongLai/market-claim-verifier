#!/bin/sh
# First run installs locked dependencies. UV_OFFLINE=1 also disables package downloads.
set -eu

repo_dir=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
for tool in uv python3 node; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        printf 'Missing prerequisite: %s (see AGENTS.md)\n' "$tool" >&2
        exit 1
    fi
done
node -e 'if (Number(process.versions.node.split(".")[0]) < 22) { console.error("Node 22+ is required"); process.exit(1); }'

verify_dir=$(mktemp -d "${TMPDIR:-/tmp}/claimcheck-verify.XXXXXX")
trap 'rm -rf "$verify_dir"' EXIT HUP INT TERM
export UV_CACHE_DIR="${UV_CACHE_DIR:-${TMPDIR:-/tmp}/claimcheck-verify-uv-cache}"
export UV_PYTHON_DOWNLOADS=never
export PYTHONDONTWRITEBYTECODE=1

printf 'Installing locked test dependencies (no model or SEC requests)...\n'
UV_PROJECT_ENVIRONMENT="$verify_dir/product-env" uv sync --quiet --frozen \
    --project "$repo_dir" --python "${VERIFY_PYTHON:-python3}" --no-editable
UV_PROJECT_ENVIRONMENT="$verify_dir/demo-env" uv sync --quiet --frozen \
    --project "$repo_dir/demo" --python "${VERIFY_PYTHON:-python3}"

"$verify_dir/product-env/bin/python" "$repo_dir/scripts/verify.py" \
    --work-dir "$verify_dir" --demo-python "$verify_dir/demo-env/bin/python"
