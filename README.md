# 🏈 CFB Power Index V2

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://cfb-power-index-v2.streamlit.app)

**2025 Season Analysis + 2026 Preseason Projections** · Verified QB situations · Transfer portal intelligence · Game predictor with weather adjustments

---

## Live App

👉 **[cfb-power-index-v2.streamlit.app](https://cfb-power-index-v2.streamlit.app)**

---

## What This Is

A full college football analytics platform combining:
- **V1** — 2025 season retrospective: composite efficiency rankings, CFP validation (9/11 bracket games correct), win probability model
- **V2** — 2026 preseason projections: roster continuity, verified QB situations, transfer portal intelligence, recruiting talent, coaching continuity, schedule strength

---

## The 6 Tabs

| Tab | What it does |
|-----|-------------|
| **📊 2026 Rankings** | Top 10 cards, filterable bar chart (conference / movement / QB status), "why this team ranks here" explainer |
| **🔍 Team Intel** | Per-team deep dive — 2025 efficiency profile, 2026 component radar, verified QB card with real stats, portal additions, schedule |
| **🏆 2025 CFP History** | Power Index vs committee scatter, bracket retrodiction, CFP seed vs rank analysis |
| **⚔️ Game Predictor** | Head-to-head win probability with weather adjustments + interactive QB assigner (what if a portal QB suited up?) |
| **🔬 Portal Lab** | Transfer tier system (Elite/Proven/Raw), team hauls, upside targets, all 2026 QB situations |
| **📐 Methodology** | V1 and V2 model specs, data file status, QB data sourcing |

---

## 2026 Model — 8 Components

| Component | Weight | Source |
|-----------|--------|--------|
| Prior-Year Team Quality | **35%** | 2025 efficiency stats |
| Returning Production | **20%** | CBS Sports starters data |
| QB Room | **12%** | Verified 2026 starters (hardcoded from ESPN/CBS) |
| Transfer Impact | **10%** | 247Sports portal rankings |
| Recruiting Talent | **8%** | CFBD 5-year composite |
| Coaching Continuity | **7%** | Staff retention data |
| Schedule Strength | **5%** | 2026 opponent quality |
| Context | **3%** | Game-level factors |

**Missing data defaults to neutral 50/100** — the model always runs and flags what's real vs estimated.

---

## Verified 2026 QB Data (Key Corrections)

| Team | QB | Type | 2025 Stats |
|------|----|------|-----------|
| Ohio State | Julian Sayin | Returning | 3,610 yds / 32 TD / 77.0% comp (Big Ten record) |
| Texas | Arch Manning | Returning | 3,163 yds / 26 TD / 7 INT |
| Miami (FL) | Darian Mensah | Transfer (Duke) | 3,973 yds / 34 TD / 6 INT |
| LSU | Sam Leavitt | Transfer (ASU) | 4,652 career yds / 36 TD |
| Penn State | Rocco Becht | Transfer (Iowa State) | 9,275 career yds / 64 TD |
| Auburn | Byrum Brown | Transfer (USF) | 3,158 yds / 28 TD + 1,008 rush yds |
| Oklahoma State | Drew Mestemaker | Transfer (North Texas) | 4,379 yds / 34 TD (led FBS) |

---

## Running Locally

```bash
git clone https://github.com/awhite121/cfb-power-index-v2.git
cd cfb-power-index-v2
pip install -r requirements.txt
python model_v2.py           # builds cfb_power_index_v2.csv
streamlit run app_v2.py
```

Requires `cfb_combined_data.xlsx` in the root directory for V1 features.

---

## Project Structure

```
cfb-power-index-v2/
├── app_v2.py                    # Combined V1+V2 Streamlit app (6 tabs)
├── model_v2.py                  # Model engine — builds all component scores
├── cfb_power_index_v2.csv       # Generated V2 output
├── cfb_combined_data.xlsx       # 2025 base stats (V1 + V2 prior-year quality)
├── requirements.txt
├── data/
│   ├── raw/                     # API + manual source data
│   └── processed/               # Generated model output
└── scripts/
    └── 01_pull_cfbd_data.py     # CFBD API puller
```

---

## Author

**Andrew White** — MSBA, University of Texas at Austin McCombs School of Business

[![GitHub](https://img.shields.io/badge/GitHub-awhite121-181717?logo=github)](https://github.com/awhite121)
[![Portfolio](https://img.shields.io/badge/Portfolio-andrewwhitedata.com-c8aa6e)](https://andrewwhitedata.com)
