#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
PYTHON_BIN="${PYTHON_BIN:-python3}"
"$PYTHON_BIN" -c 'import sys; assert (3, 11) <= sys.version_info[:2] < (3, 15), "Use standard CPython 3.11, 3.12, 3.13, or 3.14."'
if [[ -L .venv || ( -e .venv && ! -f .venv/pyvenv.cfg ) ]]; then
  echo "Refusing an unexpected .venv path. Rename it yourself before setup." >&2
  exit 1
fi
if [[ ! -f .venv/pyvenv.cfg ]]; then
  "$PYTHON_BIN" -m venv .venv
fi
.venv/bin/python -c 'import sys; assert (3, 11) <= sys.version_info[:2] < (3, 15), "Existing venv has an unsupported Python version."'
if grep -Eq '^[a-zA-Z0-9]' requirements.txt; then
  .venv/bin/python -m pip install --only-binary=:all: --disable-pip-version-check -r requirements.txt
  .venv/bin/python -m pip check
fi
.venv/bin/python -m unittest discover -s tests -v
echo "Setup and tests finished. See README.md for the demo command."
