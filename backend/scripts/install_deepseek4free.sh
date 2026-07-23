#!/usr/bin/env bash
# Clone/update exactly the requested provider in a local, ignored vendor folder.
# Run this after activating backend/.venv.
set -euo pipefail

if [[ -z "${VIRTUAL_ENV:-}" ]]; then
  echo "Activate backend/.venv before running this script." >&2
  exit 1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENDOR="$ROOT/.vendor/deepseek4free"
REPO="https://github.com/xtekky/deepseek4free.git"

mkdir -p "$ROOT/.vendor"
if [[ -d "$VENDOR/.git" ]]; then
  git -C "$VENDOR" pull --ff-only
else
  rm -rf "$VENDOR"
  git clone --depth 1 "$REPO" "$VENDOR"
fi
python -m pip install -r "$VENDOR/requirements.txt"
echo "DeepSeek4Free is ready at $VENDOR"
echo "Set DEEPSEEK_AUTH_TOKEN in backend/.env before starting the server."
