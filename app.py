import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import StandardScaler

# ─── Page Config ─────────────────────────────────────────────
st.set_page_config(
    page_title="CFB Power Index Dashboard",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ──────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800;900&family=Source+Sans+3:wght@300;400;600;700&display=swap');

    /* Global */
    .stApp { background-color: #0c0f1a; color: #d0d3e0; }
    section[data-testid="stSidebar"] { background-color: #10132a; border-right: 1px solid #1e2240; }
    h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: #eae7e0 !important; }
    h4 { color: #d4c9a8 !important; }
    p, li, span, div { color: #c8cbd8; }
    .stMarkdown p { color: #c8cbd8 !important; }
    strong, b { color: #e8e5dc !important; }
    code { color: #e0c97f !important; }

    /* Header banner */
    .hero-banner {
        background: linear-gradient(135deg, #10132a 0%, #1a1535 50%, #10132a 100%);
        border: 1px solid #252850;
        border-radius: 12px;
        padding: 28px 36px 22px;
        margin-bottom: 24px;
    }
    .hero-banner h1 {
        font-size: 2.2rem;
        background: linear-gradient(135deg, #c8aa6e 0%, #e8d5a8 50%, #c8aa6e 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 0 4px 0;
    }
    .hero-banner p { color: #9a9eb8 !important; font-size: 0.92rem; margin: 0; }

    /* KPI cards */
    .kpi-card {
        background: linear-gradient(135deg, #12152e 0%, #181c38 100%);
        border: 1px solid #252850;
        border-radius: 10px;
        padding: 18px 20px;
        text-align: center;
    }
    .kpi-card .label { font-size: 0.72rem; color: #a0a4be; text-transform: uppercase; letter-spacing: 1.2px; margin-bottom: 6px; }
    .kpi-card .value { font-size: 2rem; font-weight: 800; color: #c8aa6e; font-family: 'Playfair Display', serif; }
    .kpi-card .sub { font-size: 0.75rem; color: #8a8ea8; margin-top: 4px; }

    /* Metric pill */
    .metric-pill {
        display: inline-block;
        background: rgba(200,170,110,0.08);
        border: 1px solid rgba(200,170,110,0.2);
        border-radius: 6px;
        padding: 4px 12px;
        font-size: 0.78rem;
        color: #c8aa6e;
        margin: 2px 4px 2px 0;
    }

    /* Clean table styling */
    .stDataFrame { border-radius: 8px; overflow: hidden; }
    div[data-testid="stMetric"] { background: #12152e; border: 1px solid #252850; border-radius: 10px; padding: 14px 18px; }
    div[data-testid="stMetric"] label { color: #a0a4be !important; font-size: 0.78rem !important; text-transform: uppercase; letter-spacing: 1px; }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #c8aa6e !important; font-family: 'Playfair Display', serif !important; }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid #252850; }
    .stTabs [data-baseweb="tab"] {
        background: transparent; color: #9a9eb8; border-radius: 8px 8px 0 0;
        padding: 10px 20px; font-weight: 600; font-size: 0.9rem;
    }
    .stTabs [aria-selected="true"] { background: #c8aa6e !important; color: #0c0f1a !important; }

    /* Note box */
    .note-box {
        background: rgba(200,170,110,0.06);
        border: 1px solid rgba(200,170,110,0.15);
        border-left: 3px solid #c8aa6e;
        border-radius: 6px;
        padding: 14px 18px;
        font-size: 0.85rem;
        color: #b8bcd0;
        margin: 16px 0;
    }
    .note-box strong { color: #c8aa6e; }

    /* Sidebar label colors */
    section[data-testid="stSidebar"] label { color: #c8aa6e !important; font-weight: 600 !important; }
    section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] { background: #181c38; }
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span { color: #b0b4c8 !important; }
</style>
""", unsafe_allow_html=True)

# ─── Data Loading & Processing ───────────────────────────────
@st.cache_data
def load_and_process():
    df = pd.read_excel("cfb_combined_data.xlsx")

    # Feature engineering (mirrors notebook exactly)
    df["Off_Efficiency"] = df["Off_PPG"] / df["Off_Plays"]
    df["Def_Efficiency"] = df["Def_PPG_Allowed"] / df["Def_Plays_Faced"]
    df["Explosive_Score"] = df["Off_Yds_Per_Play"] * df["Off_Efficiency"]
    df["Def_Havoc_Rate"] = df["Def_Takeaways"] / df["Def_Plays_Faced"]
    df["Net_PPG"] = df["Off_PPG"] - df["Def_PPG_Allowed"]
    df["Net_Yds_Per_Game"] = df["Off_Total_Yds"] - df["Def_TotalYds_Allowed"]

    metrics = ["Off_Efficiency", "Explosive_Score", "Def_Efficiency",
               "Def_Havoc_Rate", "Net_PPG", "Net_Yds_Per_Game"]

    # Standardize
    scaler = StandardScaler()
    z_cols = [m + "_z" for m in metrics]
    df[z_cols] = scaler.fit_transform(df[metrics])

    # Power Index with notebook weights
    weights = {
        "Off_Efficiency_z":   0.30,
        "Explosive_Score_z":  0.20,
        "Def_Efficiency_z":  -0.25,
        "Def_Havoc_Rate_z":   0.10,
        "Net_PPG_z":          0.10,
        "Net_Yds_Per_Game_z": 0.05,
    }
    df["Power_Index"] = sum(df[col] * w for col, w in weights.items())
    df["Power_Rank"] = df["Power_Index"].rank(ascending=False).astype(int)

    # CFP data
    cfp_teams = [
        "Indiana", "Ohio State", "Georgia", "Texas Tech",
        "Oregon", "Ole Miss", "Texas A&M", "Oklahoma",
        "Alabama", "Miami (FL)", "Tulane", "James Madison"
    ]
    cfp_seeds = {
        "Indiana": 1, "Ohio State": 2, "Georgia": 3, "Texas Tech": 4,
        "Oregon": 5, "Ole Miss": 6, "Texas A&M": 7, "Oklahoma": 8,
        "Alabama": 9, "Miami (FL)": 10, "Tulane": 11, "James Madison": 12
    }
    df["Made_CFP"] = df["School"].isin(cfp_teams).astype(int)
    df["CFP_Seed"] = df["School"].map(cfp_seeds)

    return df, metrics, z_cols

df, metrics, z_cols = load_and_process()

# ─── CFP & Bracket Constants ────────────────────────────────
cfp_seeds = {
    "Indiana": 1, "Ohio State": 2, "Georgia": 3, "Texas Tech": 4,
    "Oregon": 5, "Ole Miss": 6, "Texas A&M": 7, "Oklahoma": 8,
    "Alabama": 9, "Miami (FL)": 10, "Tulane": 11, "James Madison": 12
}

bracket_games = [
    ("First Round", "Alabama", "Oklahoma", "Alabama", True),
    ("First Round", "Miami (FL)", "Texas A&M", "Miami (FL)", True),
    ("First Round", "Ole Miss", "Tulane", "Ole Miss", True),
    ("First Round", "Oregon", "James Madison", "Oregon", True),
    ("Quarterfinal", "Indiana", "Alabama", "Indiana", True),
    ("Quarterfinal", "Ohio State", "Miami (FL)", "Miami (FL)", False),
    ("Quarterfinal", "Georgia", "Ole Miss", "Ole Miss", True),
    ("Quarterfinal", "Oregon", "Texas Tech", "Oregon", True),
    ("Semifinal", "Indiana", "Oregon", "Indiana", True),
    ("Semifinal", "Miami (FL)", "Ole Miss", "Miami (FL)", False),
    ("Championship", "Indiana", "Miami (FL)", "Indiana", True),
]

def win_probability(pi_a, pi_b, hfa=0.0, k=1.2):
    diff = (pi_a - pi_b) + hfa
    return 1 / (1 + np.exp(-k * diff))

# ─── Plotly Theme ────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(12,15,26,0.8)",
    font=dict(family="Source Sans 3, sans-serif", color="#c0c3d4"),
    title_font=dict(family="Playfair Display, serif", color="#eae7e0", size=18),
    hoverlabel=dict(bgcolor="#1a1d38", bordercolor="#c8aa6e", font_color="#e8e0d0"),
)
# Default axis style applied after layout
AXIS_STYLE = dict(gridcolor="#1e2240", zerolinecolor="#252850")

def styled(fig):
    """Apply default axis grid styling to a figure."""
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig
GOLD = "#c8aa6e"
BLUE = "#4a7eed"
RED = "#e05252"
GREEN = "#6ec87a"
GRAY = "#4a4e6a"

# ─── Header ──────────────────────────────────────────────────
st.markdown("""
<div class="hero-banner">
    <h1>🏈 CFB Power Index Dashboard</h1>
    <p>Composite Efficiency Ratings · 2025 FBS Season · 134 Teams · Andrew White</p>
</div>
""", unsafe_allow_html=True)

# ─── Tabs ────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Rankings", "🏟️ CFP Validation", "🏆 Bracket Predictions",
    "⚔️ Head-to-Head", "🔍 Team Explorer", "📐 Methodology"
])

# ═══════════════════════════════════════════════════════════════
# TAB 1: Rankings
# ═══════════════════════════════════════════════════════════════
with tab1:
    col_a, col_b = st.columns([3, 1])
    with col_b:
        top_n = st.selectbox("Show top", [10, 15, 25, 50, 134], index=2, key="rank_n")

    top = df.sort_values("Power_Rank").head(top_n)

    # Bar chart
    fig = go.Figure()
    colors = [GOLD if row["Made_CFP"] else BLUE for _, row in top.iterrows()]
    fig.add_trace(go.Bar(
        y=top["School"], x=top["Power_Index"],
        orientation="h", marker_color=colors,
        text=top["Power_Index"].round(3), textposition="outside",
        textfont=dict(size=11, color="#c0c3d4"),
        hovertemplate="<b>%{y}</b><br>Power Index: %{x:.3f}<br>Rank: #%{customdata}<extra></extra>",
        customdata=top["Power_Rank"],
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=f"Top {top_n} Teams by Power Index",
        height=max(450, top_n * 34),
        yaxis=dict(autorange="reversed", gridcolor="#1e2240"),
        xaxis_title="Power Index Score",
        showlegend=False,
        margin=dict(l=140, r=60, t=50, b=30),
    )
    styled(fig)

    st.plotly_chart(fig, use_container_width=True)

    # Legend
    st.markdown(
        '<span class="metric-pill">🟡 CFP Team</span> <span class="metric-pill" style="color:#4a7eed; border-color:rgba(74,126,237,0.3);">🔵 Non-CFP</span>',
        unsafe_allow_html=True
    )

    # Table
    display_cols = ["Power_Rank", "School", "Power_Index", "Off_Efficiency",
                    "Explosive_Score", "Def_Efficiency", "Def_Havoc_Rate",
                    "Net_PPG", "Net_Yds_Per_Game", "Made_CFP"]
    table_df = top[display_cols].copy()
    table_df.columns = ["Rank", "School", "Power Index", "Off Eff", "Explosive",
                        "Def Eff", "Havoc Rate", "Net PPG", "Net Yds/G", "CFP"]
    table_df["CFP"] = table_df["CFP"].map({1: "✅", 0: ""})
    st.dataframe(
        table_df.style.format({
            "Power Index": "{:.3f}", "Off Eff": "{:.4f}", "Explosive": "{:.3f}",
            "Def Eff": "{:.4f}", "Havoc Rate": "{:.4f}", "Net PPG": "{:.1f}",
            "Net Yds/G": "{:.1f}"
        }).set_properties(**{"text-align": "center"}).set_properties(
            subset=["School"], **{"text-align": "left", "font-weight": "600"}
        ),
        use_container_width=True, hide_index=True, height=min(900, top_n * 38 + 60)
    )

# ═══════════════════════════════════════════════════════════════
# TAB 2: CFP Validation
# ═══════════════════════════════════════════════════════════════
with tab2:
    cfp_df = df[df["Made_CFP"] == 1].sort_values("Power_Rank").copy()
    our_top12 = set(df.sort_values("Power_Rank").head(12)["School"])
    actual_cfp = set(cfp_seeds.keys())
    captured = len(our_top12 & actual_cfp)
    raw_top12 = set(df.sort_values("Off_Rank").head(12)["School"])
    raw_captured = len(raw_top12 & actual_cfp)

    # KPI row
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f"""<div class="kpi-card">
            <div class="label">Power Index Captures</div>
            <div class="value">{captured}/12</div>
            <div class="sub">CFP teams in our top 12</div>
        </div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div class="kpi-card">
            <div class="label">Raw Offense Captures</div>
            <div class="value">{raw_captured}/12</div>
            <div class="sub">Our index outperforms raw offense</div>
        </div>""", unsafe_allow_html=True)
    with k3:
        avg_delta = cfp_df["CFP_Seed"].sub(cfp_df["Power_Rank"]).abs().mean()
        st.markdown(f"""<div class="kpi-card">
            <div class="label">Avg |Seed − Rank| Gap</div>
            <div class="value">{avg_delta:.1f}</div>
            <div class="sub">Average rank disagreement</div>
        </div>""", unsafe_allow_html=True)

    st.write("")

    # Scatter: Power Index vs Net PPG with CFP highlighted
    col1, col2 = st.columns(2)

    with col1:
        fig_scatter = go.Figure()
        non_cfp = df[df["Made_CFP"] == 0]
        fig_scatter.add_trace(go.Scatter(
            x=non_cfp["Power_Index"], y=non_cfp["Net_PPG"],
            mode="markers", marker=dict(color=GRAY, size=6, opacity=0.4),
            name="Other FBS", hovertemplate="%{text}<br>PI: %{x:.3f}<br>Net PPG: %{y:.1f}<extra></extra>",
            text=non_cfp["School"],
        ))
        fig_scatter.add_trace(go.Scatter(
            x=cfp_df["Power_Index"], y=cfp_df["Net_PPG"],
            mode="markers+text", text=cfp_df["School"],
            textposition="top right", textfont=dict(size=10, color=GOLD),
            marker=dict(color=GOLD, size=12, line=dict(width=1.5, color="#0c0f1a")),
            name="CFP Teams",
            hovertemplate="<b>%{text}</b><br>PI: %{x:.3f}<br>Net PPG: %{y:.1f}<extra></extra>",
        ))
        fig_scatter.update_layout(
            **PLOTLY_LAYOUT, title="Power Index vs. Scoring Margin",
            xaxis_title="Power Index", yaxis_title="Net PPG", height=440,
            legend=dict(x=0.02, y=0.98, bgcolor="rgba(0,0,0,0)"),
        )
        fig_scatter.add_hline(y=0, line_dash="dash", line_color="#252850")
        fig_scatter.add_vline(x=0, line_dash="dash", line_color="#252850")
        styled(fig_scatter)

        st.plotly_chart(fig_scatter, use_container_width=True)

    with col2:
        # Seed vs Power Rank
        fig_seed = go.Figure()
        cfp_df["Diff"] = cfp_df["CFP_Seed"] - cfp_df["Power_Rank"]
        colors_seed = [GREEN if d >= 0 else RED for d in cfp_df["Diff"]]
        fig_seed.add_trace(go.Scatter(
            x=cfp_df["Power_Rank"], y=cfp_df["CFP_Seed"],
            mode="markers+text", text=cfp_df["School"],
            textposition="top right", textfont=dict(size=9, color="#c0c3d4"),
            marker=dict(color=colors_seed, size=12, line=dict(width=1.5, color="#0c0f1a")),
            hovertemplate="<b>%{text}</b><br>Power Rank: #%{x}<br>CFP Seed: #%{y}<extra></extra>",
        ))
        fig_seed.add_trace(go.Scatter(
            x=[0, 90], y=[0, 13], mode="lines",
            line=dict(dash="dash", color="#252850"), showlegend=False,
        ))
        fig_seed.update_layout(
            **PLOTLY_LAYOUT, title="CFP Seed vs. Power Index Rank",
            xaxis_title="Power Index Rank", yaxis_title="CFP Seed",
            yaxis=dict(autorange="reversed", gridcolor="#1e2240"),
            height=440, showlegend=False,
        )
        styled(fig_seed)

        st.plotly_chart(fig_seed, use_container_width=True)

    st.markdown("""<div class="note-box">
        <strong>🟢 Green dots</strong> = our index ranked them higher than the committee.
        <strong style="color:#e05252;">🔴 Red dots</strong> = committee ranked them higher.
        Points near the diagonal = agreement between index and committee.
    </div>""", unsafe_allow_html=True)

    # CFP Comparison Table
    cfp_table = cfp_df[["School", "CFP_Seed", "Power_Rank", "Off_Rank", "Power_Index", "Net_PPG"]].copy()
    cfp_table["CFP_Seed"] = cfp_table["CFP_Seed"].astype(int)
    cfp_table["Δ Seed−Rank"] = cfp_table["CFP_Seed"] - cfp_table["Power_Rank"]
    cfp_table.columns = ["School", "CFP Seed", "Power Rank", "Off Rank", "Power Index", "Net PPG", "Δ Seed−Rank"]
    st.dataframe(
        cfp_table.style.format({
            "Power Index": "{:.3f}", "Net PPG": "{:.1f}",
            "CFP Seed": "{:.0f}", "Power Rank": "{:.0f}", "Off Rank": "{:.0f}", "Δ Seed−Rank": "{:+.0f}"
        })
        .map(lambda v: "color: #6ec87a" if isinstance(v, (int, float)) and v > 0 else ("color: #e05252" if isinstance(v, (int, float)) and v < 0 else ""), subset=["Δ Seed−Rank"]),
        use_container_width=True, hide_index=True
    )

# ═══════════════════════════════════════════════════════════════
# TAB 3: Bracket Predictions
# ═══════════════════════════════════════════════════════════════
with tab3:
    correct_count = sum(1 for g in bracket_games if g[4])

    c1, c2 = st.columns([1, 3])
    with c1:
        st.markdown(f"""<div class="kpi-card">
            <div class="label">Prediction Accuracy</div>
            <div class="value">{correct_count}/11</div>
            <div class="sub">{correct_count/11*100:.0f}% of CFP games correct</div>
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown("""<div class="note-box">
            Both misses were coin-flip games: Ohio State vs Miami (FL) at 55.6% and
            Ole Miss vs Miami (FL) at 55.7%. The model correctly predicted every lopsided
            matchup and the national champion.
        </div>""", unsafe_allow_html=True)

    st.write("")

    # Build bracket results table
    rows = []
    for rnd, a, b, actual, correct in bracket_games:
        pi_a = df.loc[df["School"] == a, "Power_Index"].values[0]
        pi_b = df.loc[df["School"] == b, "Power_Index"].values[0]
        wp = win_probability(pi_a, pi_b)
        predicted = a if wp > 0.5 else b
        conf = max(wp, 1 - wp) * 100
        rows.append({
            "Round": rnd,
            "Matchup": f"{a} vs {b}",
            "Predicted": predicted,
            "Confidence": f"{conf:.1f}%",
            "Actual Winner": actual,
            "Result": "✅" if correct else "❌",
        })

    bracket_df = pd.DataFrame(rows)

    # Color rounds
    round_colors = {"First Round": BLUE, "Quarterfinal": GOLD, "Semifinal": RED, "Championship": GREEN}

    fig_bracket = go.Figure()
    for i, row in bracket_df.iterrows():
        wp_val = float(row["Confidence"].replace("%", ""))
        color = GREEN if row["Result"] == "✅" else RED
        fig_bracket.add_trace(go.Bar(
            y=[row["Matchup"]], x=[wp_val], orientation="h",
            marker_color=color, marker_opacity=0.8,
            text=f"{row['Predicted']} ({row['Confidence']})", textposition="outside",
            textfont=dict(size=11, color="#c0c3d4"),
            showlegend=False,
            hovertemplate=f"<b>{row['Round']}</b><br>{row['Matchup']}<br>Predicted: {row['Predicted']} ({row['Confidence']})<br>Actual: {row['Actual Winner']} {row['Result']}<extra></extra>",
        ))

    fig_bracket.update_layout(
        **PLOTLY_LAYOUT,
        title="CFP Game Predictions — Confidence & Accuracy",
        xaxis_title="Prediction Confidence (%)",
        xaxis=dict(range=[0, 105], gridcolor="#1e2240"),
        yaxis=dict(autorange="reversed", gridcolor="#1e2240"),
        height=520, bargap=0.3,
        margin=dict(l=180, r=20, t=50, b=40),
    )
    fig_bracket.add_vline(x=50, line_dash="dash", line_color="#252850")
    styled(fig_bracket)

    st.plotly_chart(fig_bracket, use_container_width=True)

    st.dataframe(bracket_df, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════
# TAB 4: Head-to-Head
# ═══════════════════════════════════════════════════════════════
with tab4:
    all_teams_sorted = df.sort_values("Power_Rank")["School"].tolist()

    col_left, col_mid, col_right = st.columns([2, 1, 2])
    with col_left:
        team_a = st.selectbox("Team A", all_teams_sorted, index=0, key="h2h_a")
    with col_mid:
        venue = st.radio("Venue", ["Neutral", f"{team_a.split(' ')[0]} Home", "Away"], key="h2h_venue", horizontal=False)
    with col_right:
        team_b = st.selectbox("Team B", all_teams_sorted, index=2, key="h2h_b")

    hfa = 0.0
    if "Home" in venue:
        hfa = 0.4
    elif "Away" in venue:
        hfa = -0.4

    row_a = df[df["School"] == team_a].iloc[0]
    row_b = df[df["School"] == team_b].iloc[0]
    prob = win_probability(row_a["Power_Index"], row_b["Power_Index"], hfa)

    # Win probability bar
    st.write("")
    prob_col1, prob_col2 = st.columns(2)
    with prob_col1:
        st.metric(team_a, f"{prob*100:.1f}%", delta=f"PI: {row_a['Power_Index']:.3f} (#{int(row_a['Power_Rank'])})")
    with prob_col2:
        st.metric(team_b, f"{(1-prob)*100:.1f}%", delta=f"PI: {row_b['Power_Index']:.3f} (#{int(row_b['Power_Rank'])})")

    # Visual probability bar
    fig_prob = go.Figure()
    fig_prob.add_trace(go.Bar(
        y=["Win Probability"], x=[prob * 100], orientation="h",
        marker_color=BLUE, name=team_a, text=f"{prob*100:.1f}%",
        textposition="inside", textfont=dict(size=16, color="white"),
    ))
    fig_prob.add_trace(go.Bar(
        y=["Win Probability"], x=[(1 - prob) * 100], orientation="h",
        marker_color=RED, name=team_b, text=f"{(1-prob)*100:.1f}%",
        textposition="inside", textfont=dict(size=16, color="white"),
    ))
    fig_prob.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(12,15,26,0.8)",
        font=dict(family="Source Sans 3, sans-serif", color="#c0c3d4"),
        barmode="stack", height=100,
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.3, traceorder="normal"),
    )
    styled(fig_prob)

    st.plotly_chart(fig_prob, use_container_width=True)

    # Radar + Stats side by side
    col_radar, col_stats = st.columns([1, 1])

    with col_radar:
        metric_labels = ["Off Eff", "Explosive", "Def Eff\n(inverted)", "Havoc Rate", "Net PPG", "Net Yds/G"]
        categories = metric_labels + [metric_labels[0]]  # close the radar

        # Normalize to percentile within all 134 teams
        z_a = [row_a[z] for z in z_cols]
        z_b = [row_b[z] for z in z_cols]
        # Invert Def_Efficiency (lower is better) for display
        z_a[2] = -z_a[2]
        z_b[2] = -z_b[2]
        # Scale to 0-100 for radar
        radar_a = [max(0, min(100, (z + 3) / 6 * 100)) for z in z_a] + [max(0, min(100, (z_a[0] + 3) / 6 * 100))]
        radar_b = [max(0, min(100, (z + 3) / 6 * 100)) for z in z_b] + [max(0, min(100, (z_b[0] + 3) / 6 * 100))]

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=radar_a, theta=categories, fill="toself",
            name=team_a, line_color=BLUE, fillcolor="rgba(74,126,237,0.2)",
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=radar_b, theta=categories, fill="toself",
            name=team_b, line_color=RED, fillcolor="rgba(224,82,82,0.15)",
        ))
        fig_radar.update_layout(
            **PLOTLY_LAYOUT, title="Efficiency Radar",
            polar=dict(
                bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(visible=True, range=[0, 100], gridcolor="#1e2240", tickfont=dict(size=8, color="#4a4e6a")),
                angularaxis=dict(gridcolor="#252850", tickfont=dict(size=10, color="#c0c3d4")),
            ),
            height=400,
            legend=dict(x=0.5, xanchor="center", y=-0.1, orientation="h"),
        )
        styled(fig_radar)

        st.plotly_chart(fig_radar, use_container_width=True)

    with col_stats:
        compare_metrics = [
            ("Power Index", "Power_Index", True),
            ("Power Rank", "Power_Rank", False),
            ("Off Efficiency", "Off_Efficiency", True),
            ("Explosive Score", "Explosive_Score", True),
            ("Def Efficiency", "Def_Efficiency", False),
            ("Havoc Rate", "Def_Havoc_Rate", True),
            ("Net PPG", "Net_PPG", True),
            ("Net Yds/Game", "Net_Yds_Per_Game", True),
            ("3rd Down Off %", "Off_3rdDown_Pct", True),
            ("3rd Down Def %", "Def_3rdDown_Pct", False),
            ("Off PPG", "Off_PPG", True),
            ("Def PPG Allowed", "Def_PPG_Allowed", False),
        ]

        comparison_rows = []
        for label, col, higher_better in compare_metrics:
            va, vb = row_a[col], row_b[col]
            a_wins = (va > vb) if higher_better else (va < vb)
            # Smart formatting per metric type
            if col == "Power_Rank":
                fmt_a, fmt_b = f"{int(va)}", f"{int(vb)}"
            elif col == "Power_Index":
                fmt_a, fmt_b = f"{va:.3f}", f"{vb:.3f}"
            elif col in ("Off_Efficiency", "Def_Efficiency", "Def_Havoc_Rate"):
                fmt_a, fmt_b = f"{va:.4f}", f"{vb:.4f}"
            elif col in ("Explosive_Score",):
                fmt_a, fmt_b = f"{va:.3f}", f"{vb:.3f}"
            else:
                fmt_a, fmt_b = f"{va:.1f}", f"{vb:.1f}"
            comparison_rows.append({
                "Metric": label,
                team_a: fmt_a,
                team_b: fmt_b,
                "Edge": "🔵" if a_wins else "🔴" if va != vb else "—",
            })
        st.dataframe(pd.DataFrame(comparison_rows), use_container_width=True, hide_index=True, height=460)

# ═══════════════════════════════════════════════════════════════
# TAB 5: Team Explorer
# ═══════════════════════════════════════════════════════════════
with tab5:
    team_pick = st.selectbox("Select a team", all_teams_sorted, index=0, key="explorer")
    row_t = df[df["School"] == team_pick].iloc[0]

    # Header metrics
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Power Rank", f"#{int(row_t['Power_Rank'])}")
    with m2:
        st.metric("Power Index", f"{row_t['Power_Index']:.3f}")
    with m3:
        st.metric("Off PPG", f"{row_t['Off_PPG']:.1f}")
    with m4:
        st.metric("Def PPG Allowed", f"{row_t['Def_PPG_Allowed']:.1f}")
    with m5:
        cfp_status = "✅ CFP" if row_t["Made_CFP"] else "❌ No"
        seed_txt = f" (#{int(row_t['CFP_Seed'])})" if pd.notna(row_t["CFP_Seed"]) else ""
        st.metric("Made CFP", f"{cfp_status}{seed_txt}")

    st.write("")
    col_profile, col_context = st.columns(2)

    with col_profile:
        # Z-score bar chart
        team_z = [row_t[z] for z in z_cols]
        metric_labels = ["Off Efficiency", "Explosive Score", "Def Efficiency",
                         "Havoc Rate", "Net PPG", "Net Yds/Game"]
        colors_bar = [GREEN if z > 0 else RED for z in team_z]
        # Invert def efficiency color (negative z = good defense)
        colors_bar[2] = GREEN if team_z[2] < 0 else RED

        fig_profile = go.Figure()
        fig_profile.add_trace(go.Bar(
            x=metric_labels, y=team_z, marker_color=colors_bar,
            text=[f"{z:+.2f}" for z in team_z], textposition="outside",
            textfont=dict(size=11, color="#c0c3d4"),
            hovertemplate="%{x}: %{y:.2f} std devs<extra></extra>",
        ))
        fig_profile.update_layout(
            **PLOTLY_LAYOUT,
            title=f"{team_pick} — Efficiency Profile vs. FBS Average",
            yaxis_title="Z-Score (std deviations from mean)",
            height=380,
        )
        fig_profile.add_hline(y=0, line_color="#252850")
        styled(fig_profile)

        st.plotly_chart(fig_profile, use_container_width=True)

    with col_context:
        # Context scatter
        fig_ctx = go.Figure()
        fig_ctx.add_trace(go.Scatter(
            x=df["Power_Index"], y=df["Net_PPG"],
            mode="markers", marker=dict(color=GRAY, size=5, opacity=0.3),
            hovertemplate="%{text}<br>PI: %{x:.3f}<extra></extra>",
            text=df["School"], name="All FBS",
        ))
        fig_ctx.add_trace(go.Scatter(
            x=[row_t["Power_Index"]], y=[row_t["Net_PPG"]],
            mode="markers+text", text=[team_pick],
            textposition="top right", textfont=dict(size=12, color=GOLD, family="Playfair Display"),
            marker=dict(color=GOLD, size=16, line=dict(width=2, color="#0c0f1a")),
            name=team_pick,
        ))
        fig_ctx.update_layout(
            **PLOTLY_LAYOUT,
            title=f"{team_pick} in Context",
            xaxis_title="Power Index", yaxis_title="Net PPG",
            height=380, showlegend=False,
        )
        styled(fig_ctx)

        st.plotly_chart(fig_ctx, use_container_width=True)

    # Win probabilities vs top teams
    st.subheader(f"{team_pick} — Win Probabilities vs. Top 10")
    top10 = df.sort_values("Power_Rank").head(10)
    top10_other = top10[top10["School"] != team_pick]

    wp_rows = []
    for _, opp in top10_other.iterrows():
        wp = win_probability(row_t["Power_Index"], opp["Power_Index"])
        wp_rows.append({"Opponent": opp["School"], "Win %": wp * 100, "Opp Rank": int(opp["Power_Rank"])})
    wp_df = pd.DataFrame(wp_rows).sort_values("Win %", ascending=True)

    colors_wp = [GREEN if w > 50 else RED for w in wp_df["Win %"]]
    fig_wp = go.Figure()
    fig_wp.add_trace(go.Bar(
        y=wp_df["Opponent"], x=wp_df["Win %"], orientation="h",
        marker_color=colors_wp,
        text=wp_df["Win %"].round(1).astype(str) + "%", textposition="outside",
        textfont=dict(size=11, color="#c0c3d4"),
    ))
    fig_wp.update_layout(
        **PLOTLY_LAYOUT, height=350, title="",
        xaxis=dict(range=[0, 105], gridcolor="#1e2240"),
        xaxis_title="Win Probability (%) — Neutral Site",
        showlegend=False,
    )
    fig_wp.add_vline(x=50, line_dash="dash", line_color="#252850")
    styled(fig_wp)

    st.plotly_chart(fig_wp, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# TAB 6: Methodology
# ═══════════════════════════════════════════════════════════════
with tab6:
    st.markdown("### How the Power Index Works")
    st.markdown("""
    The Power Index combines **six engineered efficiency metrics** into a single composite
    score. All metrics are standardized to z-scores before weighting so every dimension
    contributes on a common scale.
    """)

    col_w, col_f = st.columns(2)

    with col_w:
        st.markdown("#### Index Weights")
        w_data = pd.DataFrame({
            "Metric": ["Off Efficiency", "Explosive Score", "Def Efficiency", "Havoc Rate", "Net PPG", "Net Yds/Game"],
            "Weight": [30, 20, 25, 10, 10, 5],
            "Direction": ["↑ Higher = better", "↑ Higher = better", "↓ Lower = better (neg weight)",
                         "↑ Higher = better", "↑ Higher = better", "↑ Higher = better"],
        })
        fig_w = go.Figure()
        fig_w.add_trace(go.Bar(
            x=w_data["Weight"], y=w_data["Metric"], orientation="h",
            marker_color=GOLD, text=w_data["Weight"].astype(str) + "%",
            textposition="outside", textfont=dict(color="#c0c3d4"),
        ))
        fig_w.update_layout(**PLOTLY_LAYOUT, height=280, title="", xaxis_title="Weight (%)",
                           yaxis=dict(autorange="reversed"))
        styled(fig_w)

        st.plotly_chart(fig_w, use_container_width=True)

    with col_f:
        st.markdown("#### Feature Definitions")
        features = [
            ("**Off Efficiency**", "`PPG ÷ Plays/Game`", "Points per offensive play"),
            ("**Explosive Score**", "`Yds/Play × Off Eff`", "Big-play + scoring combo"),
            ("**Def Efficiency**", "`PPG Allowed ÷ Plays Faced`", "Points allowed per snap"),
            ("**Havoc Rate**", "`Takeaways ÷ Plays Faced`", "Turnover-forcing rate"),
            ("**Net PPG**", "`Off PPG − Def PPG Allowed`", "Scoring margin"),
            ("**Net Yds/Game**", "`Off Yds − Def Yds Allowed`", "Yardage margin"),
        ]
        for name, formula, desc in features:
            st.markdown(f"{name}: {formula} — *{desc}*")

    st.markdown("---")
    st.markdown("#### Win Probability Model")
    st.latex(r"P(A \text{ beats } B) = \frac{1}{1 + e^{-k \cdot (PI_A - PI_B + HFA)}}")
    st.markdown("""
    Where **k = 1.2** controls sensitivity and **HFA = 0.4** for home advantage (0 for neutral).
    This achieved **82% accuracy** (9/11) retrodicting the 2025–26 CFP bracket.
    """)

    # Distributions
    st.markdown("#### Engineered Metric Distributions (All 134 Teams)")
    metric_colors = [BLUE, GOLD, RED, GREEN, "#8b5cf6", "#f59e0b"]
    fig_dist = go.Figure()
    for i, m in enumerate(metrics):
        fig_dist.add_trace(go.Histogram(
            x=df[m], name=m.replace("_", " "), marker_color=metric_colors[i],
            opacity=0.7, nbinsx=25, visible=True if i == 0 else "legendonly",
        ))
    fig_dist.update_layout(
        **PLOTLY_LAYOUT, title="Distribution of Engineered Metrics",
        barmode="overlay", height=350,
    )
    styled(fig_dist)

    st.plotly_chart(fig_dist, use_container_width=True)

    # Correlation heatmap
    st.markdown("#### Metric Correlations")
    corr = df[metrics].corr()
    fig_corr = go.Figure(data=go.Heatmap(
        z=corr.values, x=[m.replace("_", " ") for m in metrics],
        y=[m.replace("_", " ") for m in metrics],
        colorscale="RdBu_r", zmid=0,
        text=corr.round(2).values, texttemplate="%{text}",
        textfont=dict(size=11),
    ))
    fig_corr.update_layout(**PLOTLY_LAYOUT, height=450, title="Correlation Matrix — Engineered Metrics",
                          margin=dict(l=120, r=20, t=50, b=20))
    styled(fig_corr)

    st.plotly_chart(fig_corr, use_container_width=True)

# ─── Sidebar ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏈 About")
    st.markdown("""
    This dashboard presents a **composite Power Index** for the 2025 FBS
    college football season, built from six efficiency metrics.

    **Author:** Andrew White
    **Data:** 134 FBS teams, 2025 season
    **Methodology:** Z-score standardization + weighted composite

    ---
    *Built for MSBA coursework · Streamlit + Plotly*
    """)

    st.markdown("### Quick Stats")
    st.metric("Total Teams", 134)
    st.metric("CFP Capture Rate", f"{len(set(df.sort_values('Power_Rank').head(12)['School']) & set(cfp_seeds.keys()))}/12")
    st.metric("Bracket Accuracy", "9/11 (82%)")
