#!/usr/bin/env bash
# One-shot deploy helper for CFB Power Index V2.
# Run it from inside the project folder:  bash push_v2.sh
set -e

REPO_URL="https://github.com/awhite121/cfb-power-index-v2.git"

echo "==> Project: $(pwd)"
if [ ! -f app_v2.py ]; then
  echo "ERROR: app_v2.py not found. cd into the project folder first, then re-run."
  exit 1
fi

echo "==> What the CSV on disk says for Texas (should be 12):"
python3 -c "import pandas as pd; d=pd.read_csv('data/processed/cfb_power_index_v2.csv'); print(d[d.team=='Texas'][['rank_v2','team','power_index_v2']].to_string(index=False))"

# Make sure this repo points at the V2 remote.
if ! git remote get-url origin >/dev/null 2>&1; then
  git remote add origin "$REPO_URL"
else
  git remote set-url origin "$REPO_URL"
fi
echo "==> Remote origin: $(git remote get-url origin)"

# Stage everything, including the rebuilt data.
git add -A
echo "==> Staged changes:"
git status --short

# Commit only if there is something to commit.
if git diff --cached --quiet; then
  echo "==> Nothing new to commit (working tree already committed)."
else
  git commit -m "Deploy V2: returning production + forward-looking weights (Texas #12)"
fi

# Ensure branch is main and push.
git branch -M main
echo "==> Pushing to origin/main ..."
git push -u origin main

echo ""
echo "==> Verifying what is now on GitHub for Texas (should be 12):"
git show HEAD:data/processed/cfb_power_index_v2.csv | grep -i "^12,\|,Texas," | grep -i texas || \
  git show HEAD:data/processed/cfb_power_index_v2.csv | grep -i texas

echo ""
echo "DONE. Now in Streamlit Cloud: open the app -> (top-right menu) -> Reboot app,"
echo "and confirm Settings has Main file path = app_v2.py."
