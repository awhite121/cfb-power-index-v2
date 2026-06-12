# CFB Power Index V2 Data Plan

## Folder structure

```text
cfb-power-index/
  app.py                         # existing V1 Streamlit app
  app_v2.py                      # V2 Streamlit app starter
  model_v2.py                    # V2 scoring logic
  requirements.txt
  .env.example                   # copy to .env locally and add your CFBD key
  data/
    raw/                         # untouched API pulls and manually collected CSVs
    processed/                   # model-ready feature tables and final scores
    templates/                   # CSV templates you can fill in manually
  scripts/
    config.py                    # paths + env loading
    cfbd_client.py               # reusable CFBD API client
    01_pull_cfbd_data.py          # pulls schedule, team stats, player stats, recruiting, weather
    02_build_features_v2.py       # builds feature-level scores
    03_build_power_index_v2.py    # builds final V2 Power Index
  docs/
    V2_DATA_PLAN.md
```

## Manual CSVs to fill first

Copy the templates into `data/raw/` and rename them:

```text
data/templates/2026_returning_production_template.csv -> data/raw/2026_returning_production.csv
data/templates/2026_transfers_template.csv -> data/raw/2026_transfers.csv
data/templates/2026_coaches_template.csv -> data/raw/2026_coaches.csv
```

## Run order

```bash
cp .env.example .env
# edit .env and add CFBD_API_KEY
pip install -r requirements.txt
python scripts/01_pull_cfbd_data.py
python scripts/02_build_features_v2.py
python scripts/03_build_power_index_v2.py
streamlit run app_v2.py
```

## Final score weights

```text
35% Prior-Year Team Quality
20% Returning Production / Roster Continuity
12% QB Situation
10% Transfer Impact
8% Recruiting Talent
7% Coaching Continuity
5% Schedule Strength
3% Special Teams / Context placeholder
```
