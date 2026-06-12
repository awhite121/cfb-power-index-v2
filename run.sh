#!/usr/bin/env bash
# Convenience runner for CFB Power Index V2.
# Usage:
#   ./run.sh setup     # create venv + install deps
#   ./run.sh diagnose  # check CFBD auth (run this if you get 401s)
#   ./run.sh pull      # pull raw data from CFBD (needs a working key)
#   ./run.sh build     # build features + final power index + coverage report
#   ./run.sh app       # launch the Streamlit app
#   ./run.sh all       # build + app
set -euo pipefail
cd "$(dirname "$0")"

PY="${PYTHON:-python3}"

case "${1:-app}" in
  setup)
    $PY -m venv .venv
    # shellcheck disable=SC1091
    source .venv/bin/activate
    python -m pip install -r requirements.txt
    ;;
  diagnose) $PY scripts/00_diagnose_cfbd.py ;;
  pull)     $PY scripts/01_pull_cfbd_data.py ;;
  build)    $PY scripts/03_build_power_index_v2.py ;;
  app)      $PY -m streamlit run app_v2.py ;;
  all)
    $PY scripts/03_build_power_index_v2.py
    $PY -m streamlit run app_v2.py
    ;;
  *) echo "Unknown command: $1"; echo "Try: setup | diagnose | pull | build | app | all"; exit 1 ;;
esac
