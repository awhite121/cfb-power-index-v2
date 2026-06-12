from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import predictor as P

st.set_page_config(
    page_title="CFB Power Index V2",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).resolve().parent
PROCESSED = ROOT / "data" / "processed" / "cfb_power_index_v2.csv"
COVERAGE = ROOT / "data" / "processed" / "coverage_report.csv"
RAW = ROOT / "data" / "raw"
EXCEL = ROOT / "cfb_combined_data.xlsx"

# ─── Custom CSS (matches the V1 dashboard design language) ───────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800;900&family=Source+Sans+3:wght@300;400;600;700&display=swap');

    .stApp { background-color: #0c0f1a; color: #d0d3e0; }
    section[data-testid="stSidebar"] { background-color: #10132a; border-right: 1px solid #1e2240; }
    h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: #eae7e0 !important; }
    h4 { color: #d4c9a8 !important; }
    p, li, span, div { color: #c8cbd8; }
    .stMarkdown p { color: #c8cbd8 !important; }
    strong, b { color: #e8e5dc !important; }
    code { color: #e0c97f !important; }

    .hero-banner {
        background: linear-gradient(135deg, #10132a 0%, #1a1535 50%, #10132a 100%);
        border: 1px solid #252850; border-radius: 12px;
        padding: 28px 36px 22px; margin-bottom: 24px;
    }
    .hero-banner h1 {
        font-size: 2.2rem;
        background: linear-gradient(135deg, #c8aa6e 0%, #e8d5a8 50%, #c8aa6e 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin: 0 0 4px 0;
    }
    .hero-banner p { color: #9a9eb8 !important; font-size: 0.92rem; margin: 0; }

    .kpi-card {
        background: linear-gradient(135deg, #12152e 0%, #181c38 100%);
        border: 1px solid #252850; border-radius: 10px;
        padding: 18px 20px; text-align: center;
    }
    .kpi-card .label { font-size: 0.72rem; color: #a0a4be; text-transform: uppercase; letter-spacing: 1.2px; margin-bottom: 6px; }
    .kpi-card .value { font-size: 2rem; font-weight: 800; color: #c8aa6e; font-family: 'Playfair Display', serif; }
    .kpi-card .sub { font-size: 0.75rem; color: #8a8ea8; margin-top: 4px; }

    .metric-pill {
        display: inline-block; background: rgba(200,170,110,0.08);
        border: 1px solid rgba(200,170,110,0.2); border-radius: 6px;
        padding: 4px 12px; font-size: 0.78rem; color: #c8aa6e; margin: 2px 4px 2px 0;
    }

    .stDataFrame { border-radius: 8px; overflow: hidden; }
    div[data-testid="stMetric"] { background: #12152e; border: 1px solid #252850; border-radius: 10px; padding: 14px 18px; }
    div[data-testid="stMetric"] label { color: #a0a4be !important; font-size: 0.78rem !important; text-transform: uppercase; letter-spacing: 1px; }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #c8aa6e !important; font-family: 'Playfair Display', serif !important; }

    .stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid #252850; flex-wrap: wrap; }
    .stTabs [data-baseweb="tab"] {
        background: transparent; color: #9a9eb8; border-radius: 8px 8px 0 0;
        padding: 10px 18px; font-weight: 600; font-size: 0.88rem;
    }
    .stTabs [aria-selected="true"] { background: #c8aa6e !important; color: #0c0f1a !important; }

    .note-box {
        background: rgba(200,170,110,0.06); border: 1px solid rgba(200,170,110,0.15);
        border-left: 3px solid #c8aa6e; border-radius: 6px;
        padding: 14px 18px; font-size: 0.85rem; color: #b8bcd0; margin: 16px 0;
    }
    .note-box strong { color: #c8aa6e; }

    .empty-box {
        background: rgba(74,126,237,0.05); border: 1px dashed #2a3160;
        border-radius: 10px; padding: 26px 28px; margin: 14px 0; color: #aeb3cc;
    }
    .empty-box h4 { color: #c8aa6e !important; margin: 0 0 6px 0; font-family: 'Playfair Display', serif; }
    .empty-box code { color: #e0c97f; }

    section[data-testid="stSidebar"] label { color: #c8aa6e !important; font-weight: 600 !important; }
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span { color: #b0b4c8 !important; }
</style>
""", unsafe_allow_html=True)

# ─── Plotly theme ────────────────────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(12,15,26,0.8)",
    font=dict(family="Source Sans 3, sans-serif", color="#c0c3d4"),
    title_font=dict(family="Playfair Display, serif", color="#eae7e0", size=18),
    hoverlabel=dict(bgcolor="#1a1d38", bordercolor="#c8aa6e", font_color="#e8e0d0"),
)
AXIS_STYLE = dict(gridcolor="#1e2240", zerolinecolor="#252850")
GOLD, BLUE, RED, GREEN, GRAY, PURPLE = "#c8aa6e", "#4a7eed", "#e05252", "#6ec87a", "#4a4e6a", "#8b5cf6"


def styled(fig):
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig


# ─── Component config ────────────────────────────────────────────────────────
SCORE_COLS = [
    "prior_year_team_quality_score", "returning_production_score", "qb_score",
    "transfer_impact_score", "recruiting_talent_score", "coaching_continuity_score",
    "schedule_strength_score", "context_score",
]
WEIGHT_LABELS = {
    "prior_year_team_quality_score": "Prior-year quality",
    "returning_production_score": "Returning production",
    "qb_score": "QB room",
    "transfer_impact_score": "Transfer impact",
    "recruiting_talent_score": "Recruiting/talent",
    "coaching_continuity_score": "Coaching continuity",
    "schedule_strength_score": "Schedule strength",
    "context_score": "Context",
}
WEIGHTS = {
    "prior_year_team_quality_score": 0.35, "returning_production_score": 0.20,
    "qb_score": 0.12, "transfer_impact_score": 0.10, "recruiting_talent_score": 0.08,
    "coaching_continuity_score": 0.07, "schedule_strength_score": 0.05, "context_score": 0.03,
}


def fmt_col(name: str) -> str:
    return WEIGHT_LABELS.get(name, name.replace("_", " ").title())


# ─── Data loaders ────────────────────────────────────────────────────────────
@st.cache_data
def load_index() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED)
    for c in SCORE_COLS + ["power_index_v2", "team_strength_rating"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


@st.cache_data
def load_excel() -> pd.DataFrame:
    if EXCEL.exists():
        x = pd.read_excel(EXCEL)
        x = x.rename(columns={"School": "team"})
        return x
    return pd.DataFrame()


@st.cache_data
def load_coverage() -> pd.DataFrame:
    if COVERAGE.exists() and COVERAGE.stat().st_size > 0:
        return pd.read_csv(COVERAGE)
    return pd.DataFrame()


def load_raw(*names) -> pd.DataFrame:
    """Return the first existing/non-empty raw CSV among the given names."""
    for name in names:
        path = RAW / name
        if path.exists() and path.stat().st_size > 0:
            try:
                return pd.read_csv(path)
            except Exception:
                continue
    return pd.DataFrame()


def empty_state(title: str, why: str, cmds: list[str]):
    cmd_html = "<br>".join(f"<code>{c}</code>" for c in cmds)
    st.markdown(
        f"""<div class="empty-box"><h4>{title}</h4>
        <p style="margin:0 0 10px 0;">{why}</p>{cmd_html}</div>""",
        unsafe_allow_html=True,
    )


def team_filter(df: pd.DataFrame, team: str, cols=("team", "School", "school")) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            return df[df[c].astype(str).str.lower() == team.lower()]
    return pd.DataFrame()


# ─── Position grouping + tidy helpers (for portal / stats) ───────────────────
_POS_GROUPS = {
    "QB": "QB", "RB": "RB", "FB": "RB", "HB": "RB", "TB": "RB",
    "WR": "WR/TE", "TE": "WR/TE",
    "OT": "OL", "OG": "OL", "G": "OL", "C": "OL", "OL": "OL", "T": "OL", "IOL": "OL",
    "DL": "DL", "DT": "DL", "NT": "DL", "DE": "EDGE", "EDGE": "EDGE",
    "LB": "LB", "ILB": "LB", "OLB": "LB", "MLB": "LB",
    "CB": "DB", "S": "DB", "SAF": "DB", "DB": "DB", "FS": "DB", "SS": "DB", "NB": "DB",
    "PK": "ST", "K": "ST", "P": "ST", "LS": "ST",
}


def pos_group(p) -> str:
    return _POS_GROUPS.get(str(p).upper().strip(), "ATH/Other")


def _scrub(series: pd.Series) -> pd.Series:
    """Turn literal 'nan'/'none'/'null'/'' strings into real NA so the UI shows
    blanks instead of the word 'nan'."""
    s = series.astype("string")
    return s.mask(s.str.strip().str.lower().isin(["nan", "none", "null", "<na>", ""]))


def clean_portal(portal: pd.DataFrame) -> pd.DataFrame:
    """Standardize the CFBD portal feed (firstName/lastName/origin/destination) into
    tidy, human-readable columns the UI can present consistently."""
    df = portal.copy()
    if "player" not in df.columns:
        fn = df.get("firstName", pd.Series("", index=df.index)).astype(str).replace("nan", "")
        ln = df.get("lastName", pd.Series("", index=df.index)).astype(str).replace("nan", "")
        df["player"] = (fn + " " + ln).str.strip()
    for c in ["origin", "destination", "position", "eligibility"]:
        if c not in df.columns:
            df[c] = None
    if "team" in df.columns and df["destination"].isna().all():
        df["destination"] = df["team"]
    # Scrub literal "nan"/"none" text out of the string columns.
    for c in ["player", "origin", "destination", "position", "eligibility"]:
        df[c] = _scrub(df[c])
    df["rating"] = pd.to_numeric(df.get("rating"), errors="coerce")
    df["stars"] = pd.to_numeric(df.get("stars"), errors="coerce")
    df["pos_group"] = df["position"].map(pos_group)
    date_src = next((c for c in ["transferDate", "date"] if c in df.columns), None)
    df["date"] = pd.to_datetime(df[date_src], errors="coerce").dt.date if date_src else None
    return df


def portal_years() -> list[str]:
    """Discover which seasons of portal data are on disk, newest first.
    Matches both {year}_transfer_portal_cfbd.csv and {year}_transfers.csv."""
    years = set()
    for pat in ["*_transfer_portal_cfbd.csv", "*_transfers.csv"]:
        for f in RAW.glob(pat):
            yr = "".join(ch for ch in f.stem[:4] if ch.isdigit())
            if len(yr) == 4:
                years.add(yr)
    return sorted(years, reverse=True)


def load_portal_year(year: str) -> pd.DataFrame:
    """Load and clean one season's portal feed."""
    raw = load_raw(f"{year}_transfer_portal_cfbd.csv", f"{year}_transfers.csv")
    return clean_portal(raw) if not raw.empty else raw


def blank_na(df: pd.DataFrame) -> pd.DataFrame:
    """Replace NaN/NaT with empty string for clean display tables."""
    return df.astype(object).where(pd.notna(df), "")


def _na(s):
    return s.astype(str).str.strip().str.lower()


idx = load_index()
excel = load_excel()
coverage = load_coverage()
prof = idx.merge(excel, on="team", how="left") if not excel.empty else idx.copy()
teams_sorted = idx.sort_values("rank_v2")["team"].tolist()

# ─── Header ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-banner">
    <h1>🏈 CFB Power Index V2</h1>
    <p>Roster-aware preseason model · Prior-year quality · Returning production · QB · Transfers · Recruiting · Coaching · Schedule · Game predictor</p>
</div>
""", unsafe_allow_html=True)

# ─── Honesty banner ──────────────────────────────────────────────────────────
if not coverage.empty:
    weighted_real = (coverage["coverage_pct"] / 100 * coverage["weight"]).sum() * 100
    live = coverage[coverage["coverage_pct"] > 0]["component"].map(fmt_col).tolist()
    missing = coverage[coverage["coverage_pct"] == 0]["component"].map(fmt_col).tolist()
    if weighted_real < 99:
        st.markdown(
            f"""<div class="note-box"><strong>Data coverage: {weighted_real:.0f}% of model weight is real.</strong>
            Live now: {', '.join(live) or 'none'}. Still neutral (50/100): {', '.join(missing)}.
            Pull CFBD data or fill the manual CSVs to light these up — see the <strong>Data Coverage</strong> tab.</div>""",
            unsafe_allow_html=True,
        )

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏈 About")
    st.markdown(
        "**CFB Power Index V2** blends prior-year quality with roster continuity, "
        "QB stability, transfer-portal impact, recruiting, coaching, and schedule into "
        "one explainable rating — plus a game predictor.\n\n**Author:** Andrew White"
    )
    st.markdown("### Quick Stats")
    st.metric("Teams", f"{len(idx):,}")
    if not idx.empty:
        st.metric("Top Team", idx.sort_values("rank_v2").iloc[0]["team"])
    if not coverage.empty:
        st.metric("Data Coverage", f"{weighted_real:.0f}%")

# ─── Tabs ────────────────────────────────────────────────────────────────────
t_rank, t_team, t_h2h, t_roster, t_sched, t_players, t_coach, t_method, t_cov = st.tabs([
    "📊 Rankings", "🔍 Team Deep Dive", "⚔️ Head-to-Head", "🔄 Roster & Portal",
    "📅 Schedule & Records", "📈 Player Stats", "🧑\u200d🏫 Coaching", "📐 Methodology", "🩺 Data Coverage",
])

# ═══════════════════════════════════════════ Rankings ═══════════════════════
with t_rank:
    c1, c2 = st.columns([3, 1])
    with c2:
        top_n = st.selectbox("Show top", [10, 15, 25, 50, len(idx)], index=2, key="rank_n")
    top = idx.sort_values("rank_v2").head(top_n)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=top["team"], x=top["power_index_v2"], orientation="h", marker_color=GOLD,
        text=top["power_index_v2"].round(1), textposition="outside",
        textfont=dict(size=11, color="#c0c3d4"),
        hovertemplate="<b>%{y}</b><br>Power Index: %{x:.1f}<br>Rank: #%{customdata}<extra></extra>",
        customdata=top["rank_v2"],
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT, title=f"Top {top_n} Teams by Power Index",
        height=max(450, top_n * 30), yaxis=dict(autorange="reversed", gridcolor="#1e2240"),
        xaxis_title="Power Index Score", showlegend=False, margin=dict(l=150, r=60, t=50, b=30),
    )
    st.plotly_chart(styled(fig), use_container_width=True)

    cols = ["rank_v2", "team", "power_index_v2", "team_strength_rating"] + [c for c in SCORE_COLS if c in top.columns]
    table = top[cols].copy()
    for c in table.columns:
        if c not in ("rank_v2", "team"):
            table[c] = pd.to_numeric(table[c], errors="coerce").round(1)
    table = table.rename(columns={
        "rank_v2": "Rank", "team": "Team", "power_index_v2": "Power Index",
        "team_strength_rating": "Team Strength", **{c: fmt_col(c) for c in SCORE_COLS}})
    st.dataframe(table, use_container_width=True, hide_index=True, height=min(900, top_n * 36 + 60))

# ═══════════════════════════════════════════ Team Deep Dive ═════════════════
with t_team:
    team = st.selectbox("Select a team", teams_sorted, index=0, key="dd_team")
    row = idx[idx["team"] == team].iloc[0]
    prow = team_filter(prof, team)
    prow = prow.iloc[0] if not prow.empty else row

    m = st.columns(5)
    m[0].metric("Power Rank", f"#{int(row['rank_v2'])}")
    m[1].metric("Power Index", f"{row['power_index_v2']:.1f}")
    m[2].metric("Strength Rank", f"#{int(row['strength_rank'])}" if "strength_rank" in row else "—")
    _qbname = str(row.get("projected_qb", "") or "").strip()
    m[3].metric("Projected QB", _qbname if _qbname and _qbname.lower() != "nan" else "—",
                delta=f"score {row.get('qb_score', 50):.0f}", delta_color="off")
    m[4].metric("Off PPG", f"{prow.get('Off_PPG', float('nan')):.1f}" if pd.notna(prow.get('Off_PPG', np.nan)) else "—")

    st.write("")
    cL, cR = st.columns(2)
    with cL:
        comp = [c for c in SCORE_COLS if c in idx.columns]
        vals = [float(row[c]) for c in comp]
        colors = [GOLD if WEIGHTS.get(c, 0) >= 0.10 else BLUE for c in comp]
        fig = go.Figure(go.Bar(
            x=[fmt_col(c) for c in comp], y=vals, marker_color=colors,
            text=[f"{v:.0f}" for v in vals], textposition="outside", textfont=dict(color="#c0c3d4"),
            hovertemplate="%{x}: %{y:.1f}/100<extra></extra>"))
        fig.update_layout(**PLOTLY_LAYOUT, title=f"{team} — Component Scores",
                          yaxis=dict(range=[0, 110], gridcolor="#1e2240"), height=390,
                          xaxis_tickangle=-30)
        st.plotly_chart(styled(fig), use_container_width=True)
    with cR:
        fig = go.Figure(go.Scatter(
            x=idx["power_index_v2"], y=idx["team_strength_rating"] if "team_strength_rating" in idx else idx["power_index_v2"],
            mode="markers", marker=dict(color=GRAY, size=6, opacity=0.35), text=idx["team"],
            hovertemplate="%{text}<extra></extra>", name="FBS"))
        fig.add_trace(go.Scatter(
            x=[row["power_index_v2"]], y=[row.get("team_strength_rating", row["power_index_v2"])],
            mode="markers+text", text=[team], textposition="top center",
            textfont=dict(color=GOLD, size=12, family="Playfair Display"),
            marker=dict(color=GOLD, size=16, line=dict(width=2, color="#0c0f1a")), name=team))
        fig.update_layout(**PLOTLY_LAYOUT, title=f"{team} in Context",
                          xaxis_title="Power Index", yaxis_title="Team Strength (schedule-free)",
                          height=390, showlegend=False)
        st.plotly_chart(styled(fig), use_container_width=True)

    breakdown = pd.DataFrame({"c": [fmt_col(c) for c in comp], "Score": vals})
    strengths = breakdown.sort_values("Score", ascending=False).head(3)["c"].tolist()
    weaknesses = breakdown.sort_values("Score").head(2)["c"].tolist()
    qb_status = row.get("qb_status", "")
    st.markdown(
        f"""<div class="note-box"><strong>Why {team} ranks #{int(row['rank_v2'])}:</strong>
        strongest components are <strong>{', '.join(strengths)}</strong>; main drag areas are
        <strong>{', '.join(weaknesses)}</strong>.{(' QB status: <code>' + str(qb_status) + '</code>.') if qb_status else ''}</div>""",
        unsafe_allow_html=True,
    )

    # ── Team hub: portal class · recruiting · schedule/SOS, all for THIS team ──
    st.markdown("---")
    st.markdown(f"### {team} — Roster Movement, Recruiting & Schedule")
    hub1, hub2, hub3 = st.columns(3)

    # Portal class for this team (latest season on file)
    with hub1:
        _yrs = portal_years()
        _yr = _yrs[0] if _yrs else None
        st.markdown(f"**🔄 Transfer Portal Class{(' — ' + _yr) if _yr else ''}**")
        _p = load_portal_year(_yr) if _yr else pd.DataFrame()
        if _p.empty:
            st.caption("No portal data loaded.")
        else:
            _in = _p[_p["destination"].astype(str) == team]
            _out = _p[_p["origin"].astype(str) == team]
            pc = st.columns(3)
            pc[0].metric("In", len(_in)); pc[1].metric("Out", len(_out))
            pc[2].metric("Net", f"{len(_in) - len(_out):+d}")
            top_adds = _in.sort_values("rating", ascending=False, na_position="last").head(5)
            if not top_adds.empty:
                st.caption("Top incoming:")
                show = top_adds[["player", "pos_group", "origin"]].rename(
                    columns={"player": "Player", "pos_group": "Pos", "origin": "From"})
                st.dataframe(blank_na(show), use_container_width=True, hide_index=True, height=190)
            st.caption("Full breakdown in the Roster & Portal tab →")

    # Recruiting class history for this team
    with hub2:
        st.markdown("**⭐ Recruiting Class History**")
        _rec = load_raw("2022_2026_recruiting.csv")
        if _rec.empty or "team" not in _rec.columns:
            st.caption("No recruiting data loaded.")
        else:
            tr = _rec[_rec["team"].astype(str) == team].copy()
            tr["year"] = pd.to_numeric(tr["year"], errors="coerce")
            tr["rank"] = pd.to_numeric(tr["rank"], errors="coerce")
            tr["points"] = pd.to_numeric(tr["points"], errors="coerce")
            tr = tr.dropna(subset=["year"]).sort_values("year")
            if tr.empty:
                st.caption("No recruiting classes on file for this team.")
            else:
                latest = tr.iloc[-1]
                rc = st.columns(2)
                rc[0].metric(f"{int(latest['year'])} Class Rank", f"#{int(latest['rank'])}" if pd.notna(latest["rank"]) else "—")
                rc[1].metric("Class Points", f"{latest['points']:.0f}" if pd.notna(latest["points"]) else "—")
                fig = go.Figure(go.Scatter(
                    x=tr["year"], y=tr["rank"], mode="lines+markers",
                    line=dict(color=GOLD, width=2), marker=dict(size=8, color=GOLD)))
                fig.update_layout(**PLOTLY_LAYOUT, height=210, title="Class rank by year (lower = better)",
                                  yaxis=dict(autorange="reversed", gridcolor="#1e2240", title="Rank"),
                                  xaxis=dict(dtick=1, title=None), margin=dict(l=40, r=20, t=40, b=30))
                st.plotly_chart(styled(fig), use_container_width=True)

    # 2026 schedule + strength of schedule for this team
    with hub3:
        st.markdown("**📅 2026 Schedule Strength**")
        _s = load_raw("2026_schedule.csv")
        hc = next((c for c in ["home_team", "homeTeam", "home"] if c in _s.columns), None)
        ac = next((c for c in ["away_team", "awayTeam", "away"] if c in _s.columns), None)
        if _s.empty or not (hc and ac):
            st.caption("No schedule data loaded.")
        else:
            tg = _s[(_s[hc] == team) | (_s[ac] == team)].copy()
            tg["Opponent"] = np.where(tg[hc] == team, tg[ac], tg[hc])
            rl = idx[["team", "rank_v2"]].rename(columns={"team": "Opponent", "rank_v2": "Opp Rank"})
            tg = tg.merge(rl, on="Opponent", how="left")
            ranked = tg["Opp Rank"].dropna()
            sc = st.columns(2)
            sc[0].metric("Games", len(tg))
            sc[1].metric("Avg Opp Rank", f"{ranked.mean():.0f}" if len(ranked) else "—")
            top5 = tg.dropna(subset=["Opp Rank"]).sort_values("Opp Rank").head(5)
            if not top5.empty:
                st.caption("Toughest opponents:")
                show = top5[["Opponent", "Opp Rank"]].copy()
                show["Opp Rank"] = show["Opp Rank"].astype(int)
                st.dataframe(blank_na(show), use_container_width=True, hide_index=True, height=190)
            st.caption("Full slate in the Schedule & Records tab →")

# ═══════════════════════════════════════════ Head-to-Head ══════════════════
with t_h2h:
    cL, cM, cR = st.columns([2, 1, 2])
    with cL:
        ta = st.selectbox("Team A", teams_sorted, index=0, key="h2h_a")
    with cM:
        venue = st.radio("Venue", ["Neutral", "Team A home", "Team B home"], key="h2h_v")
        wind = st.slider("Wind (mph)", 0, 40, 0, key="h2h_wind")
        precip = st.checkbox("Precipitation", key="h2h_precip")
    with cR:
        tb = st.selectbox("Team B", teams_sorted, index=min(2, len(teams_sorted) - 1), key="h2h_b")

    if ta == tb:
        st.info("Pick two different teams.")
    else:
        location = {"Neutral": "neutral", "Team A home": "home_a", "Team B home": "home_b"}[venue]
        weather = {"wind_speed": wind, "precipitation": 0.3 if precip else 0.0}
        pred = P.predict_game(ta, tb, df=idx, location=location, weather=weather)

        st.write("")
        p1, p2, p3 = st.columns(3)
        p1.metric(ta, f"{pred.win_prob_a*100:.1f}%")
        p2.metric("Projected", f"{pred.proj_score_a:.0f} – {pred.proj_score_b:.0f}")
        p3.metric(tb, f"{pred.win_prob_b*100:.1f}%")

        fig = go.Figure()
        fig.add_trace(go.Bar(y=["Win Prob"], x=[pred.win_prob_a * 100], orientation="h",
                             marker_color=BLUE, name=ta, text=f"{pred.win_prob_a*100:.0f}%",
                             textposition="inside", textfont=dict(size=16, color="white")))
        fig.add_trace(go.Bar(y=["Win Prob"], x=[pred.win_prob_b * 100], orientation="h",
                             marker_color=RED, name=tb, text=f"{pred.win_prob_b*100:.0f}%",
                             textposition="inside", textfont=dict(size=16, color="white")))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(12,15,26,0.8)",
                          barmode="stack", height=90, xaxis=dict(visible=False), yaxis=dict(visible=False),
                          margin=dict(l=0, r=0, t=0, b=0),
                          legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.4))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(f"""<div class="note-box">{pred.narrative}</div>""", unsafe_allow_html=True)

        cRad, cEdge = st.columns([1, 1])
        comp = [c for c in SCORE_COLS if c in idx.columns]
        ra, rb = idx[idx["team"] == ta].iloc[0], idx[idx["team"] == tb].iloc[0]
        with cRad:
            cats = [fmt_col(c) for c in comp] + [fmt_col(comp[0])]
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(r=[float(ra[c]) for c in comp] + [float(ra[comp[0]])],
                                          theta=cats, fill="toself", name=ta, line_color=BLUE,
                                          fillcolor="rgba(74,126,237,0.2)"))
            fig.add_trace(go.Scatterpolar(r=[float(rb[c]) for c in comp] + [float(rb[comp[0]])],
                                          theta=cats, fill="toself", name=tb, line_color=RED,
                                          fillcolor="rgba(224,82,82,0.15)"))
            fig.update_layout(**PLOTLY_LAYOUT, title="Component Radar",
                              polar=dict(bgcolor="rgba(0,0,0,0)",
                                         radialaxis=dict(visible=True, range=[0, 100], gridcolor="#1e2240",
                                                         tickfont=dict(size=8, color="#4a4e6a")),
                                         angularaxis=dict(gridcolor="#252850", tickfont=dict(size=9, color="#c0c3d4"))),
                              height=420, legend=dict(x=0.5, xanchor="center", y=-0.08, orientation="h"))
            st.plotly_chart(styled(fig), use_container_width=True)
        with cEdge:
            edges_df = pd.DataFrame([{
                "Factor": e.label, ta: round(e.team_a_value, 0), tb: round(e.team_b_value, 0),
                "Edge": "🔵" if e.diff > 0 else ("🔴" if e.diff < 0 else "—"), "Gap": round(abs(e.diff), 0),
            } for e in pred.edges])
            st.dataframe(edges_df, use_container_width=True, hide_index=True, height=300)
            st.markdown('<span class="metric-pill">🔵 ' + ta + '</span> '
                        '<span class="metric-pill" style="color:#e05252;border-color:rgba(224,82,82,0.3);">🔴 ' + tb + '</span>',
                        unsafe_allow_html=True)

# ═══════════════════════════════════════════ Roster & Portal ═══════════════
with t_roster:
    st.subheader("Transfer Portal — Per-Team Class")
    years_avail = portal_years()
    if not years_avail:
        empty_state(
            "No transfer-portal data yet",
            "Add incoming/outgoing transfers to light up the Transfer Impact component (position-weighted: QB &gt; OT/EDGE/CB &gt; WR/DL/LB &gt; RB).",
            ["python3 scripts/01_pull_cfbd_data.py   # pulls portal for 2023–2026 (needs a CFBD key)",
             "# each season lands as data/raw/{year}_transfer_portal_cfbd.csv"],
        )
    else:
        ctl = st.columns([1, 3])
        with ctl[0]:
            ysel = st.selectbox("Season", years_avail, index=0, key="portal_year")
        portal = load_portal_year(ysel)
        # Team universe = anyone who shows up as an origin or destination this season.
        univ = sorted({t for t in pd.concat([portal["destination"].dropna(), portal["origin"].dropna()]).astype(str).unique()
                       if t and t.lower() not in ("none", "nan")})
        with ctl[1]:
            default_team = next((t for t in teams_sorted if t in univ), univ[0] if univ else None)
            pteam = st.selectbox("Team", univ, index=univ.index(default_team) if default_team in univ else 0, key="portal_team")

        incoming = portal[portal["destination"].astype(str) == pteam].copy()
        outgoing = portal[portal["origin"].astype(str) == pteam].copy()

        net_by_grp = (incoming.groupby("pos_group").size()
                      .subtract(outgoing.groupby("pos_group").size(), fill_value=0))
        k = st.columns(4)
        k[0].metric("Incoming", len(incoming))
        k[1].metric("Outgoing", len(outgoing))
        k[2].metric("Net", f"{len(incoming) - len(outgoing):+d}")
        avg_in = pd.to_numeric(incoming["rating"], errors="coerce").mean()
        k[3].metric("Avg incoming rating", f"{avg_in:.3f}" if pd.notna(avg_in) else "—")

        cIn, cOut = st.columns(2)
        disp_cols_in = ["player", "pos_group", "position", "origin", "rating", "stars", "eligibility", "date"]
        disp_cols_out = ["player", "pos_group", "position", "destination", "rating", "stars", "eligibility", "date"]
        with cIn:
            st.markdown(f"**Incoming — {ysel}** &nbsp;<span class='metric-pill' style='color:#6ec87a;border-color:rgba(110,200,122,0.3);'>adds</span>", unsafe_allow_html=True)
            tin = incoming[[c for c in disp_cols_in if c in incoming.columns]].sort_values(
                "rating", ascending=False, na_position="last").rename(
                columns={"player": "Player", "pos_group": "Group", "position": "Pos",
                         "origin": "From", "rating": "Rating", "stars": "Stars",
                         "eligibility": "Elig", "date": "Date"})
            st.dataframe(blank_na(tin), use_container_width=True, hide_index=True, height=360)
        with cOut:
            st.markdown(f"**Outgoing — {ysel}** &nbsp;<span class='metric-pill' style='color:#e05252;border-color:rgba(224,82,82,0.3);'>losses</span>", unsafe_allow_html=True)
            tout = outgoing[[c for c in disp_cols_out if c in outgoing.columns]].sort_values(
                "rating", ascending=False, na_position="last").rename(
                columns={"player": "Player", "pos_group": "Group", "position": "Pos",
                         "destination": "To", "rating": "Rating", "stars": "Stars",
                         "eligibility": "Elig", "date": "Date"})
            st.dataframe(blank_na(tout), use_container_width=True, hide_index=True, height=360)

        st.markdown(f"#### Position-Need Analysis &nbsp;<span class='metric-pill'>{pteam} · {ysel} net adds by group</span>", unsafe_allow_html=True)
        order = ["QB", "RB", "WR/TE", "OL", "DL", "EDGE", "LB", "DB", "ST", "ATH/Other"]
        nb = net_by_grp.reindex(order).fillna(0)
        nb = nb[nb != 0] if (nb != 0).any() else nb
        colors = [GREEN if v > 0 else (RED if v < 0 else GRAY) for v in nb.values]
        fig = go.Figure(go.Bar(x=nb.values, y=nb.index, orientation="h",
                               marker_color=colors,
                               text=[f"{int(v):+d}" for v in nb.values], textposition="outside",
                               textfont=dict(color="#c0c3d4")))
        fig.update_layout(**PLOTLY_LAYOUT, height=360, title=f"{pteam} — net portal movement by position group ({ysel})",
                          xaxis_title="Net players (adds − losses)", yaxis=dict(autorange="reversed"))
        fig.add_vline(x=0, line_color="#252850")
        st.plotly_chart(styled(fig), use_container_width=True)

        # ── Year-over-year: same team across every season on file ──
        if len(years_avail) > 1:
            st.markdown(f"#### {pteam} — Portal Trend Across Seasons")
            yoy = []
            for y in sorted(years_avail):
                pf = load_portal_year(y)
                if pf.empty:
                    continue
                ti = (pf["destination"].astype(str) == pteam).sum()
                to = (pf["origin"].astype(str) == pteam).sum()
                ar = pd.to_numeric(pf.loc[pf["destination"].astype(str) == pteam, "rating"], errors="coerce").mean()
                yoy.append({"Season": y, "In": int(ti), "Out": int(to), "Net": int(ti - to),
                            "Avg In Rating": round(ar, 3) if pd.notna(ar) else None})
            yoy_df = pd.DataFrame(yoy)
            if not yoy_df.empty:
                cT, cTbl = st.columns([3, 2])
                with cT:
                    figy = go.Figure()
                    figy.add_trace(go.Bar(x=yoy_df["Season"], y=yoy_df["In"], name="In", marker_color=GREEN))
                    figy.add_trace(go.Bar(x=yoy_df["Season"], y=-yoy_df["Out"], name="Out", marker_color=RED))
                    figy.add_trace(go.Scatter(x=yoy_df["Season"], y=yoy_df["Net"], name="Net",
                                              mode="lines+markers", line=dict(color=GOLD, width=3)))
                    figy.update_layout(**PLOTLY_LAYOUT, height=320, barmode="relative",
                                       title=f"{pteam} — portal in/out by season",
                                       xaxis=dict(type="category"), yaxis_title="Players")
                    figy.add_hline(y=0, line_color="#252850")
                    st.plotly_chart(styled(figy), use_container_width=True)
                with cTbl:
                    st.dataframe(blank_na(yoy_df), use_container_width=True, hide_index=True, height=320)
        else:
            st.markdown('<div class="note-box">Only <strong>' + years_avail[0] +
                        '</strong> is on file. To compare year-over-year, run '
                        '<code>python3 scripts/01_pull_cfbd_data.py</code> (it now pulls 2023–2026) '
                        'so each season lands as <code>{year}_transfer_portal_cfbd.csv</code>.</div>',
                        unsafe_allow_html=True)

    st.subheader("Roster")
    roster = load_raw("2026_rosters.csv")
    if roster.empty:
        empty_state("No roster data yet",
                    "Rosters power position-level returning production (QB/OL continuity matters more than backup RB).",
                    ["python3 scripts/01_pull_cfbd_data.py"])
    else:
        rteam = st.selectbox("Roster — team", sorted(roster["team"].dropna().unique()) if "team" in roster else [], key="roster_team")
        st.dataframe(team_filter(roster, rteam) if rteam else roster, use_container_width=True, hide_index=True, height=420)

# ═══════════════════════════════════════════ Schedule & Records ════════════
with t_sched:
    st.subheader("2026 Schedule & Strength")
    sched = load_raw("2026_schedule.csv")
    if sched.empty:
        empty_state("No 2026 schedule yet",
                    "The schedule drives Schedule Strength (avg opponent rating, road games) and projected records.",
                    ["python3 scripts/01_pull_cfbd_data.py"])
    else:
        steam = st.selectbox("Schedule — team", teams_sorted, key="sched_team")
        # CFBD /games uses camelCase homeTeam/awayTeam; manual templates may use snake_case.
        home_col = next((c for c in ["home_team", "homeTeam", "home"] if c in sched.columns), None)
        away_col = next((c for c in ["away_team", "awayTeam", "away"] if c in sched.columns), None)
        if home_col and away_col:
            tg = sched[(sched[home_col] == steam) | (sched[away_col] == steam)].copy()
            is_home = tg[home_col] == steam
            tg["Opponent"] = np.where(is_home, tg[away_col], tg[home_col])
            neutral_col = next((c for c in ["neutral_site", "neutralSite", "neutral"] if c in tg.columns), None)
            neutral = tg[neutral_col].fillna(False).astype(bool) if neutral_col else pd.Series(False, index=tg.index)
            tg["Site"] = np.where(neutral, "Neutral", np.where(is_home, "Home", "Away"))
            wk_col = next((c for c in ["week", "Week"] if c in tg.columns), None)
            if wk_col:
                tg["Week"] = pd.to_numeric(tg[wk_col], errors="coerce")
            # Merge opponent power-index rank/score from the published index.
            rank_lookup = idx[["team", "power_index_v2", "rank_v2"]].copy()
            rank_lookup = rank_lookup.rename(columns={"team": "Opponent", "power_index_v2": "Opp Index", "rank_v2": "Opp Rank"})
            tg = tg.merge(rank_lookup, on="Opponent", how="left")
            tg["Opp Index"] = tg["Opp Index"].round(1)

            home_n = int(is_home.sum()); away_n = int((tg["Site"] == "Away").sum())
            ranked = tg["Opp Rank"].dropna()
            k = st.columns(4)
            k[0].metric("Games", len(tg)); k[1].metric("Home", home_n); k[2].metric("Away", away_n)
            k[3].metric("Avg opp rank", f"{ranked.mean():.0f}" if len(ranked) else "—")

            show_cols = [c for c in ["Week", "Opponent", "Site", "Opp Rank", "Opp Index"] if c in tg.columns]
            tg_view = tg.sort_values("Week" if "Week" in tg.columns else "Opponent")[show_cols]
            st.dataframe(blank_na(tg_view), use_container_width=True, hide_index=True, height=380)
        else:
            st.dataframe(sched, use_container_width=True, hide_index=True, height=360)

    st.subheader("2025 Standings & Records — FBS")
    records = load_raw("2025_records.csv")
    if records.empty:
        empty_state("No prior-season records yet",
                    "Win/loss, home/away splits, and conference records come from the CFBD /records endpoint.",
                    ["python3 scripts/01_pull_cfbd_data.py"])
    else:
        rec = records.copy()
        # CFBD /records mixes FBS/FCS/D-II/D-III. Show only FBS so standings are readable.
        if "classification" in rec.columns:
            rec = rec[rec["classification"].astype(str).str.lower() == "fbs"]
        rename = {
            "team": "Team", "conference": "Conference",
            "total.wins": "W", "total.losses": "L", "total.ties": "T",
            "conferenceGames.wins": "Conf W", "conferenceGames.losses": "Conf L",
            "homeGames.wins": "Home W", "homeGames.losses": "Home L",
            "awayGames.wins": "Away W", "awayGames.losses": "Away L",
            "expectedWins": "Exp Wins",
        }
        have = {k: v for k, v in rename.items() if k in rec.columns}
        rdf = rec[list(have.keys())].rename(columns=have)
        if "Exp Wins" in rdf.columns:
            rdf["Exp Wins"] = pd.to_numeric(rdf["Exp Wins"], errors="coerce").round(1)
        confs = sorted(rdf["Conference"].dropna().unique()) if "Conference" in rdf.columns else []
        csel = st.selectbox("Conference", ["All"] + confs, key="rec_conf")
        view = rdf if csel == "All" else rdf[rdf["Conference"] == csel]
        sort_col = "W" if "W" in view.columns else view.columns[0]
        view = view.sort_values(sort_col, ascending=False)
        st.caption(f"{len(view):,} FBS teams")
        st.dataframe(blank_na(view), use_container_width=True, hide_index=True, height=440)

# ═══════════════════════════════════════════ Player Stats ══════════════════
with t_players:
    # ── Top Returning QBs: ranked by the model's QB score, with 2025 stat line ──
    st.subheader("Top Returning QBs (2026 projection)")
    qb_cols = [c for c in ["projected_qb", "qb_score", "qb_status"] if c in idx.columns]
    if {"projected_qb", "qb_score"}.issubset(idx.columns):
        qb = idx[["team", "rank_v2"] + qb_cols].copy()
        qb = qb[qb["projected_qb"].astype(str).str.strip().str.lower().ne("nan") & qb["projected_qb"].notna()]
        # Attach each QB's 2025 passing line so it's clear what the score is built on.
        try:
            _ps = pd.read_csv(RAW / "2025_player_stats.csv")
            _pa = _ps[_ps["category"].astype(str).str.lower() == "passing"].copy()
            _pa["stat"] = pd.to_numeric(_pa["stat"], errors="coerce")
            _pw = _pa.pivot_table(index=["player", "team"], columns="statType", values="stat", aggfunc="first").reset_index()
            _pw.columns.name = None
            qb = qb.merge(_pw, left_on=["projected_qb", "team"], right_on=["player", "team"], how="left")
        except Exception:
            for c in ["YDS", "TD", "INT", "PCT", "YPA"]:
                qb[c] = np.nan
        qb = qb.sort_values("qb_score", ascending=False)
        show_cols = ["projected_qb", "team", "qb_score", "YDS", "TD", "INT", "PCT", "YPA"]
        lead = qb[[c for c in show_cols if c in qb.columns]].head(30).rename(columns={
            "projected_qb": "QB", "team": "Team", "qb_score": "QB Score",
            "YDS": "2025 Yds", "TD": "2025 TD", "INT": "2025 INT", "PCT": "Comp %", "YPA": "Yds/Att"})
        for c in ["QB Score", "Comp %", "Yds/Att"]:
            if c in lead.columns:
                lead[c] = pd.to_numeric(lead[c], errors="coerce").round(1)
        for c in ["2025 Yds", "2025 TD", "2025 INT"]:
            if c in lead.columns:
                lead[c] = pd.to_numeric(lead[c], errors="coerce").round(0)
        st.caption("Each team's projected 2026 starter = its 2025 primary passer (assumes return). Score blends YPA, TD, completion %, INT avoidance, and volume.")
        st.dataframe(blank_na(lead), use_container_width=True, hide_index=True, height=420)
    st.markdown("---")

    st.subheader("Player Stats — last few seasons")
    frames = []
    for f in sorted(RAW.glob("*player_stats*.csv")):
        try:
            d = pd.read_csv(f)
            if "season" not in d.columns:
                # infer season from filename like 2025_player_stats.csv
                yr = "".join(ch for ch in f.stem[:4] if ch.isdigit())
                d["season"] = yr or f.stem
            frames.append(d)
        except Exception:
            continue
    players = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if players.empty:
        empty_state("No player stats yet",
                    "Hold multiple seasons of player stats here to power QB scoring and position-level returning production.",
                    ["python3 scripts/01_pull_cfbd_data.py   # pulls 2025 player + game stats",
                     "# add more seasons as 2024_player_stats.csv, 2023_player_stats.csv, ..."])
    elif {"category", "statType", "stat"}.issubset(players.columns):
        # CFBD /stats/player/season is LONG: one row per (player, category, statType).
        # Pivot to real stat lines so each player is a single row per category.
        fc = st.columns(3)
        cats = sorted(players["category"].dropna().astype(str).str.lower().unique())
        default_cat = "passing" if "passing" in cats else (cats[0] if cats else None)
        catsel = fc[0].selectbox("Category", cats, index=cats.index(default_cat) if default_cat in cats else 0, key="ps_cat")
        seasons = sorted(players["season"].astype(str).dropna().unique())
        ssel = fc[1].selectbox("Season", ["All"] + seasons, key="ps_season")
        teams_in = sorted(players["team"].dropna().unique()) if "team" in players else []
        tsel = fc[2].selectbox("Team", ["All"] + teams_in, key="ps_team")

        sub = players[players["category"].astype(str).str.lower() == catsel].copy()
        if ssel != "All":
            sub = sub[sub["season"].astype(str) == ssel]
        if tsel != "All" and "team" in sub:
            sub = sub[sub["team"] == tsel]

        sub["stat"] = pd.to_numeric(sub["stat"], errors="coerce")
        idx_cols = [c for c in ["player", "team", "position", "season"] if c in sub.columns]
        wide = sub.pivot_table(index=idx_cols, columns="statType", values="stat", aggfunc="first").reset_index()
        wide.columns.name = None
        # Sort by the most meaningful volume stat available for this category.
        sort_pref = ["YDS", "TOT", "SACKS", "PTS", "REC", "INT", "TD", "ATT"]
        sort_col = next((c for c in sort_pref if c in wide.columns), None)
        if sort_col:
            wide = wide.sort_values(sort_col, ascending=False, na_position="last")
        ren = {"player": "Player", "team": "Team", "position": "Pos", "season": "Season"}
        wide = wide.rename(columns={k: v for k, v in ren.items() if k in wide.columns})
        st.caption(f"{len(wide):,} players — {catsel}")
        st.dataframe(blank_na(wide), use_container_width=True, hide_index=True, height=460)
    else:
        # Fallback for wide-format files.
        fc = st.columns(3)
        tcol = "team" if "team" in players else ("School" if "School" in players else None)
        psel = fc[0].selectbox("Team", ["All"] + (sorted(players[tcol].dropna().unique()) if tcol else []), key="ps_team")
        ssel = fc[1].selectbox("Season", ["All"] + sorted(players["season"].astype(str).dropna().unique()), key="ps_season")
        possel = fc[2].selectbox("Position", ["All"] + (sorted(players["position"].dropna().unique()) if "position" in players else []), key="ps_pos")
        v = players.copy()
        if psel != "All" and tcol:
            v = v[v[tcol] == psel]
        if ssel != "All":
            v = v[v["season"].astype(str) == ssel]
        if possel != "All" and "position" in v:
            v = v[v["position"] == possel]
        st.caption(f"{len(v):,} rows")
        st.dataframe(v, use_container_width=True, hide_index=True, height=460)

# ═══════════════════════════════════════════ Coaching ══════════════════════
with t_coach:
    st.subheader("Coaching Continuity & Staff Changes")
    coaches = load_raw("2026_coaches.csv")
    if coaches.empty:
        empty_state("No coaching data yet",
                    "Track HC/OC/DC retention and scheme changes. Returning QB + returning OC is a big stability signal; New HC + new coordinators is a red flag.",
                    ["cp data/templates/2026_coaches_template.csv data/raw/2026_coaches.csv"])
    else:
        st.dataframe(coaches, use_container_width=True, hide_index=True, height=420)
        ret_cols = [c for c in ["head_coach_retained", "oc_retained", "dc_retained"] if c in coaches.columns]
        if ret_cols and "team" in coaches.columns:
            cc = coaches.copy()
            cc["stability"] = cc[ret_cols].apply(pd.to_numeric, errors="coerce").fillna(0).sum(axis=1)
            cc = cc.sort_values("stability", ascending=False).head(20)
            fig = px.bar(cc, x="stability", y="team", orientation="h",
                         range_x=[0, len(ret_cols)], title="Staff retention (HC + OC + DC)")
            fig.update_layout(**PLOTLY_LAYOUT, height=460, yaxis=dict(autorange="reversed"))
            st.plotly_chart(styled(fig), use_container_width=True)

# ═══════════════════════════════════════════ Methodology ═══════════════════
with t_method:
    st.markdown("### How the V2 Power Index Works")
    cW, cF = st.columns(2)
    with cW:
        st.markdown("#### Component Weights")
        wdf = pd.DataFrame({"Component": [fmt_col(c) for c in WEIGHTS], "Weight": [w * 100 for w in WEIGHTS.values()]})
        fig = go.Figure(go.Bar(x=wdf["Weight"], y=wdf["Component"], orientation="h", marker_color=GOLD,
                               text=wdf["Weight"].astype(int).astype(str) + "%", textposition="outside",
                               textfont=dict(color="#c0c3d4")))
        fig.update_layout(**PLOTLY_LAYOUT, height=330, xaxis_title="Weight (%)", yaxis=dict(autorange="reversed"))
        st.plotly_chart(styled(fig), use_container_width=True)
    with cF:
        st.markdown("#### Key Modeling Choices")
        st.markdown(
            "- **Team strength vs. schedule are separated.** The published index includes "
            "schedule, but `team_strength_rating` excludes it — the predictor uses strength only, "
            "so a hard schedule never makes a team better at *beating* an opponent.\n"
            "- **QB and OL continuity** matter more than RB continuity.\n"
            "- **Transfer impact is position-weighted:** QB > OT/EDGE/CB > WR/DL/LB > RB.\n"
            "- **Coaching** rewards retained HC/OC/DC and penalizes scheme changes.\n"
            "- **Missing data defaults to a neutral 50/100** and is flagged in Data Coverage."
        )
    st.markdown("---")
    st.markdown("#### Game Predictor Math")
    st.latex(r"P(A\text{ beats }B) = \Phi\!\left(\frac{(R_A - R_B) + \text{HFA}}{\sigma}\right)")
    st.markdown(
        "Each team's 0–100 strength is standardized to a **points scale** (≈11 pts per "
        "standard deviation). Margin = rating gap + home-field advantage (**2.4 pts**, 0 at "
        "neutral). Win probability uses the normal model with a single-game outcome "
        "**σ ≈ 16 points**. Projected total starts at the FBS average (**≈51**) and is split by "
        "the margin; wind and precipitation lower the total and compress the favorite's edge."
    )

# ═══════════════════════════════════════════ Data Coverage ═════════════════
with t_cov:
    st.subheader("What's real vs. neutral filler")
    if not coverage.empty:
        cov = coverage.copy()
        cov["component"] = cov["component"].map(fmt_col)
        fig = px.bar(cov, x="coverage_pct", y="component", orientation="h", range_x=[0, 100],
                     color="coverage_pct", color_continuous_scale=[(0, RED), (0.5, GOLD), (1, GREEN)],
                     title="% of teams with real (non-default) data per component")
        fig.update_layout(**PLOTLY_LAYOUT, height=380, yaxis=dict(autorange="reversed"),
                          xaxis_title="Coverage %", coloraxis_showscale=False)
        st.plotly_chart(styled(fig), use_container_width=True)

    st.markdown("#### Raw data files")
    expected = {
        "2026_schedule.csv": "Schedule strength + projected records",
        "2025_records.csv": "Past standings, home/away records",
        "2025_player_stats.csv": "Player stats / QB scoring",
        "2026_rosters.csv": "Position-level returning production",
        "2026_returning_production.csv": "Returning production score",
        "2026_qb_rooms.csv": "QB score",
        "2026_transfers.csv": "Transfer impact score",
        "2026_coaches.csv": "Coaching continuity score",
        "2022_2026_recruiting.csv": "Recruiting talent score",
    }
    checks = []
    for name, feeds in expected.items():
        path = RAW / name
        ok = path.exists() and path.stat().st_size > 0
        rows = 0
        if ok:
            try:
                rows = len(pd.read_csv(path))
            except Exception:
                rows = "read error"
        checks.append({"File": name, "Feeds": feeds, "Status": "✅ Found" if ok else "⬜ Missing", "Rows": rows})
    st.dataframe(pd.DataFrame(checks), use_container_width=True, hide_index=True)
    st.markdown(
        """<div class="note-box">Fastest path to lighting these up: fix CFBD auth
        (<code>python3 scripts/00_diagnose_cfbd.py</code>) then
        <code>python3 scripts/01_pull_cfbd_data.py</code>, or copy the templates in
        <code>data/templates/</code> into <code>data/raw/</code> and fill them. Then rebuild with
        <code>python3 scripts/03_build_power_index_v2.py</code>.</div>""",
        unsafe_allow_html=True,
    )
