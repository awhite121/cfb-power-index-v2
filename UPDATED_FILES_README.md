# CFB Power Index V2 — Updated Files

V2 adds: a points-scaled team-strength rating (schedule separated from quality),
an explainable game predictor, a CFBD auth diagnostic, retry/tier-aware API
client, and a data-coverage report so you always know what's real vs. filler.

## Run locally

```bash
cd ~/Downloads/cfb-power-index-main
./run.sh setup          # venv + install deps   (or do the steps below manually)
./run.sh build          # build rankings + coverage report
./run.sh app            # launch the app
```

Manual equivalent:

```bash
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 scripts/03_build_power_index_v2.py
python3 -m streamlit run app_v2.py
```

## If CFBD returns 401

```bash
./run.sh diagnose       # or: python3 scripts/00_diagnose_cfbd.py
```

It pinpoints whether it's a bad key, an unactivated key, a paid-tier endpoint, or
a header/format issue. See `docs/CFBD_401_DIAGNOSIS.md` for the full guide.

## Add your API key

Create `.env` in the repo root:

```dotenv
CFBD_API_KEY=your_actual_key_here
```

Do not commit `.env`.

## Pull API data

After your key is saved:

```bash
python3 scripts/01_pull_cfbd_data.py
python3 scripts/03_build_power_index_v2.py
python3 -m streamlit run app_v2.py
```

## Main files

- `app_v2.py` — V2 app: Rankings, Deep Dive, Compare Teams, **Game Predictor**,
  Roster+QB, Transfers+Coaches, **Data Coverage**, Methodology. Honest coverage
  banner up top.
- `predictor.py` — explainable game prediction engine (win prob, projected score,
  per-component edges, plain-English rationale).
- `model_v2.py` — V2 scoring model. Now also outputs `team_strength_rating`
  (schedule-independent) and a `coverage_report.csv`.
- `scripts/00_diagnose_cfbd.py` — **NEW** CFBD auth diagnostic.
- `scripts/cfbd_client.py` — hardened: retries, tier-aware errors, `check_auth()`.
- `scripts/01_pull_cfbd_data.py` — API pull script.
- `scripts/02_build_features_v2.py` — writes `team_features_v2.csv`.
- `scripts/03_build_power_index_v2.py` — writes rankings + coverage report.
- `run.sh` — one-command setup / diagnose / pull / build / app.
- `docs/CFBD_401_DIAGNOSIS.md` — 401 root-cause guide.

## Manual CSVs to fill next

Copy the template files from `data/templates/` to `data/raw/` and replace example rows with real data:

```bash
cp data/templates/2026_returning_production_template.csv data/raw/2026_returning_production.csv
cp data/templates/2026_qb_rooms_template.csv data/raw/2026_qb_rooms.csv
cp data/templates/2026_transfers_template.csv data/raw/2026_transfers.csv
cp data/templates/2026_coaches_template.csv data/raw/2026_coaches.csv
```

Then rebuild:

```bash
python3 scripts/03_build_power_index_v2.py
```
