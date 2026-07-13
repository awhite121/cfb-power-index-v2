"""
CFB Power Index — Combined V1 + V2
2025 Season Analysis + 2026 Forward-Looking Projections
Andrew White · MSBA UT Austin McCombs
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os, re

def zscore(frame):
    """Column-wise standardization (mean 0, std 1), matching sklearn's
    StandardScaler (population std, ddof=0). Returns a numpy array."""
    a = np.asarray(frame, dtype=float)
    mean = a.mean(axis=0)
    std = a.std(axis=0)
    std[std == 0] = 1.0
    return (a - mean) / std

st.set_page_config(page_title="CFB Power Index", page_icon="🏈",
                   layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800;900&family=Inter:wght@300;400;500;600;700&display=swap');
.stApp{background:#0a0d1a;color:#d0d3e0}
section[data-testid="stSidebar"]{background:#0d1020;border-right:1px solid #1a1d30}
h1,h2,h3{font-family:'Playfair Display',serif!important;color:#eae7e0!important}
h4{color:#c8aa6e!important}
p,li,span,div{color:#c8cbd8}
strong,b{color:#e8e5dc!important}
.stMarkdown p{color:#c8cbd8!important}
.hero{background:linear-gradient(135deg,#0d1020 0%,#161830 50%,#0d1020 100%);border:1px solid #1e2240;border-radius:14px;padding:28px 40px 24px;margin-bottom:20px}
.hero h1{font-size:2.4rem;background:linear-gradient(135deg,#c8aa6e 0%,#f0d898 50%,#c8aa6e 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0 0 6px}
.hero p{color:#7a7ea8!important;font-size:.9rem;margin:0}
.top10-card{background:linear-gradient(135deg,#111428 0%,#181c38 100%);border:1px solid #1e2240;border-radius:10px;padding:14px 16px;text-align:center}
.top10-card .rnk{font-size:1.8rem;font-weight:900;color:#c8aa6e;font-family:'Playfair Display',serif;line-height:1}
.top10-card .team{font-size:.82rem;font-weight:600;color:#eae7e0;margin:4px 0 2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.top10-card .idx{font-size:.95rem;font-weight:700;color:#c8aa6e;font-family:monospace}
.top10-card .delta{font-size:.7rem;font-weight:600;margin-top:3px}
.top10-card .qb{font-size:.68rem;color:#7a7ea8;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.kpi{background:linear-gradient(135deg,#111428,#181c38);border:1px solid #1e2240;border-radius:10px;padding:16px 18px;text-align:center}
.kpi .lbl{font-size:.68rem;color:#8a8ea8;text-transform:uppercase;letter-spacing:1.2px;margin-bottom:5px}
.kpi .val{font-size:1.8rem;font-weight:800;color:#c8aa6e;font-family:'Playfair Display',serif}
.kpi .sub{font-size:.7rem;color:#5a5e7a;margin-top:3px}
.note{background:rgba(200,170,110,.06);border:1px solid rgba(200,170,110,.15);border-left:3px solid #c8aa6e;border-radius:6px;padding:12px 16px;font-size:.82rem;color:#b0b4c8;margin:12px 0}
.note strong{color:#c8aa6e}
.stTabs [data-baseweb="tab-list"]{gap:4px;border-bottom:1px solid #1e2240}
.stTabs [data-baseweb="tab"]{background:transparent;color:#7a7ea8;border-radius:8px 8px 0 0;padding:9px 18px;font-weight:600;font-size:.85rem}
.stTabs [aria-selected="true"]{background:#c8aa6e!important;color:#0a0d1a!important}
div[data-testid="stMetric"]{background:#111428;border:1px solid #1e2240;border-radius:10px;padding:14px 18px}
div[data-testid="stMetric"] label{color:#8a8ea8!important;font-size:.75rem!important;text-transform:uppercase;letter-spacing:1px}
div[data-testid="stMetric"] [data-testid="stMetricValue"]{color:#c8aa6e!important;font-family:'Playfair Display',serif!important}
</style>
""", unsafe_allow_html=True)

# ─── Verified 2026 QB Data ──────────────────────────────────────────────────
QB_2026 = {
    "Ohio State":    {"qb":"Julian Sayin",     "type":"returning","yds":3610,"td":32,"int":8, "cmp":77.0,"ypa":9.2,"score":92},
    "Texas":         {"qb":"Arch Manning",     "type":"returning","yds":3163,"td":26,"int":7, "cmp":72.0,"ypa":8.8,"score":88},
    "Ole Miss":      {"qb":"T. Chambliss",     "type":"returning","yds":3937,"td":22,"int":3, "cmp":66.1,"ypa":8.9,"score":86},
    "Georgia":       {"qb":"Gunner Stockton",  "type":"returning","yds":2894,"td":24,"int":5, "cmp":64.0,"ypa":8.2,"score":84},
    "Miami (FL)":    {"qb":"Darian Mensah",    "type":"transfer", "yds":3973,"td":34,"int":6, "cmp":66.8,"ypa":9.1,"score":83},
    "Notre Dame":    {"qb":"CJ Carr",          "type":"returning","yds":2741,"td":24,"int":6, "cmp":66.6,"ypa":9.4,"score":82},
    "Oklahoma State":{"qb":"Drew Mestemaker",  "type":"transfer", "yds":4379,"td":34,"int":9, "cmp":68.9,"ypa":9.5,"score":82},
    "Oregon":        {"qb":"Dante Moore",      "type":"returning","yds":3565,"td":30,"int":10,"cmp":71.8,"ypa":8.5,"score":80},
    "LSU":           {"qb":"Sam Leavitt",      "type":"transfer", "yds":1628,"td":10,"int":3, "cmp":60.7,"ypa":8.1,"score":78},
    "Auburn":        {"qb":"Byrum Brown",      "type":"transfer", "yds":3158,"td":28,"int":7, "cmp":66.3,"ypa":8.4,"score":77},
    "Penn State":    {"qb":"Rocco Becht",      "type":"transfer", "yds":2584,"td":16,"int":9, "cmp":64.0,"ypa":7.8,"score":76},
    "USC":           {"qb":"Jayden Maiava",    "type":"returning","yds":3711,"td":24,"int":10,"cmp":65.8,"ypa":8.0,"score":74},
    "Nebraska":      {"qb":"A. Colandrea",     "type":"transfer", "yds":3459,"td":23,"int":9, "cmp":65.9,"ypa":8.4,"score":74},
    "Vanderbilt":    {"qb":"Diego Pavia",      "type":"returning","yds":3192,"td":27,"int":8, "cmp":65.0,"ypa":8.2,"score":72},
    "Michigan":      {"qb":"Bryce Underwood",  "type":"returning","yds":2428,"td":11,"int":9, "cmp":65.0,"ypa":7.4,"score":72},
    "Indiana":       {"qb":"Josh Hoover",      "type":"transfer", "yds":3472,"td":29,"int":13,"cmp":65.9,"ypa":8.1,"score":72},
    "Texas A&M":     {"qb":"Marcel Reed",      "type":"returning","yds":3169,"td":25,"int":12,"cmp":62.1,"ypa":7.6,"score":70},
    "South Carolina":{"qb":"LaNorris Sellers", "type":"returning","yds":2437,"td":13,"int":8, "cmp":60.8,"ypa":7.4,"score":68},
    "Oklahoma":      {"qb":"John Mateer",      "type":"returning","yds":2885,"td":14,"int":11,"cmp":62.2,"ypa":7.2,"score":66},
    "Arizona State": {"qb":"Cutter Boley",     "type":"transfer", "yds":2160,"td":15,"int":12,"cmp":65.8,"ypa":7.5,"score":64},
    "Tennessee":     {"qb":"TBD (open battle)","type":"battle",   "yds":0,"td":0,"int":0,"cmp":0,"ypa":0,"score":55},
    "Alabama":       {"qb":"Mack vs Russell",  "type":"battle",   "yds":0,"td":0,"int":0,"cmp":0,"ypa":0,"score":52},
    "Clemson":       {"qb":"TBD (Klubnik gone)","type":"battle",  "yds":0,"td":0,"int":0,"cmp":0,"ypa":0,"score":48},
    "Florida":       {"qb":"T. Jones Jr. (FR)","type":"freshman", "yds":0,"td":0,"int":0,"cmp":0,"ypa":0,"score":45},
    "Texas Tech":    {"qb":"Sorsby (risk)",    "type":"battle",   "yds":0,"td":0,"int":0,"cmp":0,"ypa":0,"score":50},
}

PORTAL_ELITES = [
    ("Elite",  "Sam Leavitt",     "QB",    "Arizona State","LSU",           0.99,"4,652 career yds/36 TD","Day-1 Starter","$4M+"),
    ("Elite",  "Cam Coleman",     "WR",    "Auburn",       "Texas",         0.97,"708 yds/5 TD (2025)",   "Day-1 Starter","$3M+"),
    ("Elite",  "Drew Mestemaker", "QB",    "North Texas",  "Oklahoma State",0.97,"4,379 yds/34 TD (FBS lead)","Day-1 Starter","$7M/2yr"),
    ("Elite",  "Darian Mensah",   "QB",    "Duke",         "Miami (FL)",    0.96,"3,973 yds/34 TD/6 INT", "Day-1 Starter","$10M"),
    ("Elite",  "Rocco Becht",     "QB",    "Iowa State",   "Penn State",    0.95,"9,275 career yds/64 TD","Day-1 Starter","N/A"),
    ("Elite",  "Byrum Brown",     "QB",    "South Florida","Auburn",        0.94,"3,158 yds/28 TD+1,008 rush","Day-1 Starter","N/A"),
    ("Elite",  "JJ Buchanan",     "WR/TE", "Utah",         "Michigan",      0.94,"427 yds/5 TD (FR 2025)","Top-3 WR","N/A"),
    ("Proven", "A. Colandrea",    "QB",    "UNLV",         "Nebraska",      0.88,"3,459 yds/23 TD (MW leader)","Day-1 Starter","N/A"),
    ("Proven", "Josh Hoover",     "QB",    "TCU",          "Indiana",       0.86,"3,472 yds/29 TD/13 INT","Day-1 Starter","N/A"),
    ("Proven", "J.H. Daley",      "EDGE",  "Utah",         "Michigan",      0.90,"10.5 TFL/7.5 sacks",    "Starter","N/A"),
    ("Proven", "Dylan Raiola",    "QB",    "Nebraska",     "Oregon",        0.90,"2025 Nebraska starter",  "Backup/RS","N/A"),
    ("Raw",    "Nick Marsh",      "WR",    "Michigan State","Indiana",      0.86,"733 yds/6 TD (2025)",    "Starter","N/A"),
    ("Raw",    "James Smith",     "DL",    "Alabama",      "Ohio State",    0.88,"6.5 sacks (2025)",       "Rotational","N/A"),
    ("Raw",    "Koi Perich",      "S",     "Minnesota",    "Oregon",        0.88,"5 INT/78 tackles",       "Starter","N/A"),
]

# V1 CFP constants
CFP_SEEDS = {
    "Indiana":1,"Ohio State":2,"Georgia":3,"Texas Tech":4,
    "Oregon":5,"Ole Miss":6,"Texas A&M":7,"Oklahoma":8,
    "Alabama":9,"Miami (FL)":10,"Tulane":11,"James Madison":12
}
BRACKET = [
    ("First Round","Alabama","Oklahoma","Alabama",True,87.7),
    ("First Round","Miami (FL)","Texas A&M","Miami (FL)",True,81.1),
    ("First Round","Ole Miss","Tulane","Ole Miss",True,68.6),
    ("First Round","Oregon","James Madison","Oregon",True,51.3),
    ("Quarterfinal","Indiana","Alabama","Indiana",True,70.3),
    ("Quarterfinal","Ohio State","Miami (FL)","Miami (FL)",False,55.6),
    ("Quarterfinal","Georgia","Ole Miss","Ole Miss",True,80.7),
    ("Quarterfinal","Oregon","Texas Tech","Oregon",True,73.9),
    ("Semifinal","Indiana","Oregon","Indiana",True,79.6),
    ("Semifinal","Miami (FL)","Ole Miss","Miami (FL)",False,55.7),
    ("Championship","Indiana","Miami (FL)","Indiana",True,64.1),
]

COMPONENTS = [
    ("prior_year_team_quality_score","Prior-Year Quality",35),
    ("returning_production_score","Returning Production",20),
    ("qb_score","QB Room",12),
    ("transfer_impact_score","Transfer Impact",10),
    ("recruiting_talent_score","Recruiting/Talent",8),
    ("coaching_continuity_score","Coaching",7),
    ("schedule_strength_score","Schedule Strength",5),
    ("context_score","Context",3),
]

# v2/CFBD school names -> the legacy names used in v1's Excel data, QB_2026,
# and PORTAL_ELITES. Without this, teams like Miami/BYU/Pitt/UConn crash the
# Team Intel tab (IndexError) and silently lose QB/portal data elsewhere.
NAME_ALIAS_V2_TO_V1={
    "App State":"Appalachian State","BYU":"Brigham Young","Hawai'i":"Hawaii",
    "Miami":"Miami (FL)","Middle Tennessee":"Middle Tennessee State",
    "NC State":"North Carolina State","Pittsburgh":"Pitt",
    "San José State":"San Jose State","Southern Miss":"Southern Mississippi",
    "UConn":"Connecticut","UL Monroe":"Louisiana-Monroe",
}
def to_v1_name(name): return NAME_ALIAS_V2_TO_V1.get(name,name)
NAME_ALIAS_V1_TO_V2={v:k for k,v in NAME_ALIAS_V2_TO_V1.items()}
def to_v2_name(name): return NAME_ALIAS_V1_TO_V2.get(name,name)

GOLD="#c8aa6e"; BLUE="#4a7eed"; RED="#e05252"; GREEN="#6ec87a"; GRAY="#3a3e5a"; PURPLE="#a87ee6"
PL=dict(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(10,13,26,.85)",
        font=dict(family="Inter,sans-serif",color="#b0b4c8"),
        title_font=dict(family="Playfair Display,serif",color="#eae7e0",size=17),
        hoverlabel=dict(bgcolor="#161830",bordercolor="#c8aa6e",font_color="#e8e0d0"))
AX=dict(gridcolor="#161a2e",zerolinecolor="#1e2240")
def sf(f): f.update_xaxes(**AX); f.update_yaxes(**AX); return f
def gc(row,col,d=50):
    try: return float(row[col]) if col in row.index and pd.notna(row[col]) else d
    except: return d

# ─── Data Loading ─────────────────────────────────────────────────────────────
@st.cache_data
def load_v2():
    for p in ["cfb_power_index_v2.csv","data/processed/cfb_power_index_v2.csv"]:
        if os.path.exists(p): return pd.read_csv(p)
    return pd.DataFrame()

@st.cache_data
def load_v1():
    """Compute V1 Power Index from raw 2025 stats."""
    for p in ["cfb_combined_data.xlsx","data/raw/cfb_combined_data.xlsx"]:
        if not os.path.exists(p): continue
        df = pd.read_excel(p)
        df["Off_Efficiency"] = df["Off_PPG"] / df["Off_Plays"]
        df["Def_Efficiency"] = df["Def_PPG_Allowed"] / df["Def_Plays_Faced"]
        df["Explosive_Score"] = df["Off_Yds_Per_Play"] * df["Off_Efficiency"]
        df["Def_Havoc_Rate"] = df["Def_Takeaways"] / df["Def_Plays_Faced"]
        df["Net_PPG"] = df["Off_PPG"] - df["Def_PPG_Allowed"]
        df["Net_Yds"] = df["Off_Total_Yds"] - df["Def_TotalYds_Allowed"]
        metrics=["Off_Efficiency","Explosive_Score","Def_Efficiency","Def_Havoc_Rate","Net_PPG","Net_Yds"]
        z=zscore(df[metrics])
        df["Power_Index"]=0.30*z[:,0]+0.20*z[:,1]-0.25*z[:,2]+0.10*z[:,3]+0.10*z[:,4]+0.05*z[:,5]
        df["Power_Rank"]=df["Power_Index"].rank(ascending=False).astype(int)
        df["Made_CFP"]=df["School"].isin(CFP_SEEDS.keys()).astype(int)
        df["CFP_Seed"]=df["School"].map(CFP_SEEDS)
        return df
    return pd.DataFrame()

@st.cache_data
def load_sched():
    for p in ["data/raw/2026_schedule.csv","2026_schedule.csv"]:
        if os.path.exists(p): return pd.read_csv(p)
    return pd.DataFrame()

v2=load_v2(); v1=load_v1(); sched_df=load_sched()

# Normalize V2 column names
if not v2.empty and "School" not in v2.columns:
    for alt in ["team","Team","school"]:
        if alt in v2.columns: v2=v2.rename(columns={alt:"School"}); break
if not v2.empty:
    if "rank_v2" not in v2.columns:
        for alt in ["Rank_2026","power_rank_v2"]:
            if alt in v2.columns: v2=v2.rename(columns={alt:"rank_v2"}); break
    if "delta_vs_2025" not in v2.columns: v2["delta_vs_2025"]=0
    if "Rank_2025" not in v2.columns: v2["Rank_2025"]=v2.get("rank_v2",pd.Series(range(1,len(v2)+1)))
    v2["qb_name"]=v2["School"].map(lambda s:QB_2026.get(to_v1_name(s),{}).get("qb","Unknown"))
    v2["qb_type"]=v2["School"].map(lambda s:QB_2026.get(to_v1_name(s),{}).get("type","unknown"))

has_v1 = not v1.empty
has_v2 = not v2.empty
df_main = v2 if has_v2 else v1  # primary df for team lists
if has_v2:
    teams_sorted=v2.sort_values("rank_v2")["School"].tolist()
elif has_v1:
    teams_sorted=v1.sort_values("Power_Rank")["School"].tolist()
else:
    teams_sorted=[]

def win_prob(pi_a,pi_b,hfa=0,k=1.2):
    return 1/(1+np.exp(-k*((pi_a-pi_b)+hfa)))

# ─── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>🏈 CFB Power Index</h1>
  <p>2025 Season Analysis + 2026 Preseason Projections · Verified QB situations · Transfer portal intelligence · Game predictor · Andrew White</p>
</div>""", unsafe_allow_html=True)

if not has_v1 and not has_v2:
    st.error("No data found. Run `python model_v2.py` to generate `cfb_power_index_v2.csv` and ensure `cfb_combined_data.xlsx` is present.")
    st.stop()

# ─── TABS ─────────────────────────────────────────────────────────────────────
tab1,tab2,tab3,tab4,tab5,tab6 = st.tabs([
    "📊 2026 Rankings",
    "🔍 Team Intel",
    "🏆 2025 CFP History",
    "⚔️ Game Predictor",
    "🔬 Portal Lab",
    "📐 Methodology",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: 2026 RANKINGS
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    if not has_v2:
        st.warning("V2 model data not found. Run `python model_v2.py` to generate rankings.")
    else:
        f1,f2,f3,f4=st.columns([2,2,2,1])
        with f1:
            conf_opts=["All"]+sorted(v2["conference"].dropna().unique().tolist()) if "conference" in v2.columns else ["All"]
            cf=st.selectbox("Conference",conf_opts,key="cf")
        with f2: mf=st.selectbox("Movement",["All","Risers (↑5+)","Fallers (↓5+)","Stable"],key="mf")
        with f3: qf=st.selectbox("QB Status",["All","Returning","Transfer","Battle"],key="qf")
        with f4: top_n=st.selectbox("Show",[10,15,25,50,len(v2)],index=2,key="rn")

        disp=v2.copy()
        if cf!="All" and "conference" in v2.columns: disp=disp[disp["conference"]==cf]
        if mf=="Risers (↑5+)": disp=disp[disp["delta_vs_2025"]>=5]
        elif mf=="Fallers (↓5+)": disp=disp[disp["delta_vs_2025"]<=-5]
        elif mf=="Stable": disp=disp[disp["delta_vs_2025"].abs()<5]
        if qf=="Returning": disp=disp[disp["qb_type"]=="returning"]
        elif qf=="Transfer": disp=disp[disp["qb_type"]=="transfer"]
        elif qf=="Battle": disp=disp[disp["qb_type"].isin(["battle","unknown","freshman"])]
        disp=disp.sort_values("rank_v2").head(top_n)

        # Top 10 cards
        st.markdown("#### ⚡ Top 10 — 2026 Preseason")
        top10=v2.sort_values("rank_v2").head(10)
        cols=st.columns(10)
        for i,(_,r) in enumerate(top10.iterrows()):
            d=int(r.get("delta_vs_2025",0))
            dc="#6ec87a" if d>0 else ("#e05252" if d<0 else "#5a5e7a")
            ds=f"↑{d}" if d>0 else(f"↓{abs(d)}" if d<0 else "—")
            qn=r.get("qb_name","?"); qs=qn[:12]+"…" if len(qn)>13 else qn
            cols[i].markdown(f"""<div class="top10-card">
              <div class="rnk">#{int(r['rank_v2'])}</div>
              <div class="team">{r['School']}</div>
              <div class="idx">{r['power_index_v2']:.1f}</div>
              <div class="delta" style="color:{dc}">{ds}</div>
              <div class="qb">{qs}</div>
            </div>""",unsafe_allow_html=True)

        st.write("")
        colors=[GREEN if d>2 else(RED if d<-2 else GOLD) for d in disp["delta_vs_2025"]]
        fig=go.Figure()
        fig.add_trace(go.Bar(y=disp["School"],x=disp["power_index_v2"],orientation="h",
            marker_color=colors,text=[f"{v:.1f}" for v in disp["power_index_v2"]],
            textposition="outside",textfont=dict(size=11,color="#9a9eb8"),
            customdata=np.stack([disp["Rank_2025"],disp["delta_vs_2025"],disp["qb_name"],disp["qb_type"]],axis=-1),
            hovertemplate="<b>%{y}</b><br>PI: %{x:.1f}<br>2025 Rank: #%{customdata[0]}<br>Δ: %{customdata[1]:+.0f}<br>QB: %{customdata[2]} (%{customdata[3]})<extra></extra>"))
        fig.update_layout(**PL,title=f"Top {top_n} — 2026 Power Index",
            height=max(420,len(disp)*30),yaxis=dict(autorange="reversed"),
            xaxis_title="Power Index (0-100)",showlegend=False,
            margin=dict(l=150,r=70,t=45,b=20))
        sf(fig); st.plotly_chart(fig,use_container_width=True)
        st.markdown('<span style="font-size:.78rem;color:#5a5e7a">🟢 Riser vs 2025  🟡 Stable  🔴 Faller</span>',unsafe_allow_html=True)

        # Why explainer
        st.markdown("#### Why does a team rank here?")
        et=st.selectbox("Select team",teams_sorted,key="et")
        er=v2[v2["School"]==et].iloc[0]
        s2=sorted([(c[1],gc(er,c[0])) for c in COMPONENTS],key=lambda x:-x[1])
        t3=[s for s in s2 if s[1]>=65][:3]; w2=[s for s in s2 if s[1]<52][:2]
        qbi=QB_2026.get(to_v1_name(et),{})
        msg=f"**{et}** ranks **#{int(er['rank_v2'])}** (was #{int(er['Rank_2025'])}, Δ{int(er['delta_vs_2025']):+d}). "
        if t3: msg+="Strengths: "+", ".join(f"**{n}** ({v:.0f})" for n,v in t3)+". "
        if w2: msg+="Concerns: "+", ".join(f"{n} ({v:.0f})" for n,v in w2)+". "
        qt=qbi.get("type","unknown")
        if qt=="returning": msg+=f"QB **{qbi.get('qb','?')}** returns (score {qbi.get('score',50)})."
        elif qt=="transfer": msg+=f"Transfer QB **{qbi.get('qb','?')}** arrives (score {qbi.get('score',50)}, first-year system discount applied)."
        else: msg+="⚠️ QB situation unresolved — model uncertainty elevated."
        st.markdown(f'<div class="note">{msg}</div>',unsafe_allow_html=True)

        # Full table
        st.markdown("#### Full Rankings")
        show=["rank_v2","School","power_index_v2","Rank_2025","delta_vs_2025","qb_name","qb_type"]
        show=[c for c in show if c in v2.columns or c in["qb_name","qb_type"]]
        tbl=disp[show].copy()
        tbl.columns=["Rank","Team","PI V2","2025","Δ","QB","QB Type"]
        tbl["Δ"]=tbl["Δ"].apply(lambda x:f"{int(x):+d}")
        st.dataframe(tbl.style.format({"PI V2":"{:.1f}"}),use_container_width=True,
                     hide_index=True,height=min(900,len(tbl)*38+40))

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: TEAM INTEL (combined V1 + V2)
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    team=st.selectbox("Select team",teams_sorted,key="ti")

    # Get both V1 and V2 rows
    r2=v2[v2["School"]==team].iloc[0] if has_v2 else None
    _r1match=v1[v1["School"]==to_v1_name(team)] if has_v1 else pd.DataFrame()
    r1=_r1match.iloc[0] if not _r1match.empty else None
    qbi=QB_2026.get(to_v1_name(team),{})

    # KPI row
    k1,k2,k3,k4,k5=st.columns(5)
    with k1:
        if r2 is not None: st.metric("2026 V2 Rank",f"#{int(r2['rank_v2'])}")
    with k2:
        if r2 is not None: st.metric("V2 Power Index",f"{r2['power_index_v2']:.1f}")
    with k3:
        if r1 is not None: st.metric("2025 Rank",f"#{int(r1['Power_Rank'])}")
    with k4:
        if r2 is not None:
            d=int(r2["delta_vs_2025"])
            st.metric("Movement",f"{d:+d}",delta="Riser" if d>0 else("Faller" if d<0 else "Stable"))
    with k5:
        if r1 is not None: st.metric("2025 PI",f"{r1['Power_Index']:.3f}")

    # V1 vs V2 comparison bars
    if r1 is not None and r2 is not None:
        st.markdown("#### 2025 vs. 2026 — Component Comparison")
        v1_metrics={"Off Eff":r1.get("Off_Efficiency",0),"Explosive":r1.get("Explosive_Score",0),
                    "Def Eff":r1.get("Def_Efficiency",0),"Havoc":r1.get("Def_Havoc_Rate",0),
                    "Net PPG":r1.get("Net_PPG",0),"Net Yds":r1.get("Net_Yds",0)}

    # QB Card
    st.markdown("#### QB Room — 2026")
    qt=qbi.get("type","unknown")
    qlbl={"returning":"✅ Returning Starter","transfer":"🔄 Transfer Starter",
          "battle":"⚠️ Open Battle","freshman":"🆕 Freshman","unknown":"❓ Unknown"}.get(qt,"❓")
    if qbi.get("yds",0)>0:
        st.markdown(f"""<div class="kpi" style="text-align:left;padding:16px 20px">
          <div style="font-size:1.1rem;font-weight:700;color:#eae7e0;margin-bottom:8px">
            {qbi.get('qb','?')} &nbsp;<span style="font-size:.78rem;color:#7a7ea8">{qlbl}</span>
          </div>
          <div style="display:flex;gap:22px;flex-wrap:wrap">
            <div><span style="color:#7a7ea8;font-size:.68rem">PASS YDS</span><br><b style="color:#c8aa6e;font-size:1.1rem">{qbi['yds']:,}</b></div>
            <div><span style="color:#7a7ea8;font-size:.68rem">TD</span><br><b style="color:#6ec87a;font-size:1.1rem">{qbi['td']}</b></div>
            <div><span style="color:#7a7ea8;font-size:.68rem">INT</span><br><b style="color:#e05252;font-size:1.1rem">{qbi['int']}</b></div>
            <div><span style="color:#7a7ea8;font-size:.68rem">CMP%</span><br><b style="color:#eae7e0;font-size:1.1rem">{qbi['cmp']:.1f}%</b></div>
            <div><span style="color:#7a7ea8;font-size:.68rem">YPA</span><br><b style="color:#eae7e0;font-size:1.1rem">{qbi['ypa']:.1f}</b></div>
            <div><span style="color:#7a7ea8;font-size:.68rem">QB SCORE</span><br><b style="color:#c8aa6e;font-size:1.1rem">{qbi['score']}/100</b></div>
          </div>
        </div>""",unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="note"><strong>{qbi.get("qb","?")}</strong> — {qlbl}. No 2025 stats available.</div>',unsafe_allow_html=True)

    st.write("")

    # Radar (V2 components) + 2025 efficiency bar
    cr,cb=st.columns(2)
    if r2 is not None:
        cats=[c[1] for c in COMPONENTS if c[0] in v2.columns]
        vals=[gc(r2,c[0]) for c in COMPONENTS if c[0] in v2.columns]
        with cr:
            st.markdown("#### 2026 Component Radar")
            cc=cats+[cats[0]]; vc=vals+[vals[0]]
            fr=go.Figure()
            fr.add_trace(go.Scatterpolar(r=vc,theta=cc,fill="toself",
                line_color=GOLD,fillcolor="rgba(200,170,110,.18)",name="2026 V2"))
            fr.update_layout(**PL,height=360,
                polar=dict(bgcolor="rgba(0,0,0,0)",
                    radialaxis=dict(visible=True,range=[0,100],gridcolor="#161a2e",tickfont=dict(size=8,color="#4a4e6a")),
                    angularaxis=dict(gridcolor="#1e2240",tickfont=dict(size=9,color="#b0b4c8"))))
            st.plotly_chart(fr,use_container_width=True)

    if r1 is not None:
        with cb:
            st.markdown("#### 2025 Efficiency Profile")
            eff_labels=["Off Efficiency","Explosive Score","Def Efficiency","Havoc Rate","Net PPG/100","Net Yds/100"]
            all_v1=v1[["Off_Efficiency","Explosive_Score","Def_Efficiency","Def_Havoc_Rate","Net_PPG","Net_Yds"]].copy()
            zz=zscore(all_v1)
            row_z=zz[v1.index.get_loc(r1.name)]
            bc2=[GREEN if z>0 else RED for z in row_z]
            # flip def_efficiency sign (lower is better)
            bc2[2]=GREEN if row_z[2]<0 else RED
            fb=go.Figure(go.Bar(x=eff_labels,y=row_z,marker_color=bc2,
                text=[f"{z:+.2f}" for z in row_z],textposition="outside",
                textfont=dict(size=11,color="#9a9eb8")))
            fb.update_layout(**PL,height=360,yaxis_title="Z-Score vs FBS Avg",
                margin=dict(l=20,r=20,t=40,b=60))
            sf(fb); st.plotly_chart(fb,use_container_width=True)

    # Scouting report
    if r2 is not None:
        s3=sorted([(c[1],gc(r2,c[0])) for c in COMPONENTS],key=lambda x:-x[1])
        t3s=[s for s in s3 if s[1]>=65][:3]; w2s=[s for s in s3 if s[1]<52][:2]
        rpt=f"**{team}** projects **#{int(r2['rank_v2'])}** entering 2026 (Δ{int(r2['delta_vs_2025']):+d} vs 2025). "
        if t3s: rpt+="Strengths: "+", ".join(f"**{n}** ({v:.0f})" for n,v in t3s)+". "
        if w2s: rpt+="Concerns: "+", ".join(f"{n} ({v:.0f})" for n,v in w2s)+". "
        if qt in("battle","freshman","unknown"): rpt+="⚠️ QB unresolved — highest model uncertainty."
        elif qt=="transfer": rpt+=f"Transfer QB {qbi.get('qb','?')} — first-year system discount applied."
        st.markdown(f'<div class="note">{rpt}</div>',unsafe_allow_html=True)

    # Portal additions
    st.markdown("#### 2026 Portal Additions")
    tp=[p for p in PORTAL_ELITES if p[4]==to_v1_name(team)]
    if tp:
        pdf=pd.DataFrame([{"Tier":t,"Player":pl,"Pos":po,"From":fr,"Rating":f"{rt:.2f}","2025 Stat":st2,"Role":ro,"NIL":ni}
                          for t,pl,po,fr,_,rt,st2,ro,ni in tp])
        st.dataframe(pdf,use_container_width=True,hide_index=True)
    else:
        st.info("No top-tier verified portal additions in the hardcoded set for this team.")

    # Schedule
    if not sched_df.empty:
        st.markdown("#### 2026 Schedule")
        hc="home_team" if "home_team" in sched_df.columns else "homeTeam"
        ac="away_team" if "away_team" in sched_df.columns else "awayTeam"
        if hc in sched_df.columns:
            games=sched_df[(sched_df[hc]==team)|(sched_df[ac]==team)].head(13).copy()
            games["Site"]=games.apply(lambda g:"Home" if g[hc]==team else("Neutral" if g.get("neutral_site",False) else "Away"),axis=1)
            games["Opponent"]=games.apply(lambda g:g[ac] if g[hc]==team else g[hc],axis=1)
            if "week" in games.columns: games=games.rename(columns={"week":"Wk"})
            sc=["Wk","Opponent","Site"] if "Wk" in games.columns else ["Opponent","Site"]
            st.dataframe(games[sc],use_container_width=True,hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: 2025 CFP HISTORY (V1)
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### 🏆 2025 CFP — Power Index Retrospective")
    if not has_v1:
        st.warning("Needs `cfb_combined_data.xlsx`. Place it in the app directory.")
    else:
        # KPI row
        our_top12=set(v1.sort_values("Power_Rank").head(12)["School"])
        actual_cfp=set(CFP_SEEDS.keys())
        captured=len(our_top12 & actual_cfp)
        correct=sum(1 for g in BRACKET if g[4])
        k1,k2,k3=st.columns(3)
        with k1: st.markdown(f'<div class="kpi"><div class="lbl">CFP Capture Rate</div><div class="val">{captured}/12</div><div class="sub">Teams in our top 12</div></div>',unsafe_allow_html=True)
        with k2: st.markdown(f'<div class="kpi"><div class="lbl">Bracket Accuracy</div><div class="val">{correct}/11</div><div class="sub">{correct/11*100:.0f}% games correct</div></div>',unsafe_allow_html=True)
        with k3: st.markdown(f'<div class="kpi"><div class="lbl">Champion</div><div class="val">Indiana</div><div class="sub">Predicted before playoff ✅</div></div>',unsafe_allow_html=True)

        st.write("")
        col1,col2=st.columns(2)

        # Power Index vs Scoring Margin scatter
        with col1:
            st.markdown("#### Power Index vs. Scoring Margin (2025)")
            cfp_df=v1[v1["Made_CFP"]==1]
            non_cfp=v1[v1["Made_CFP"]==0]
            fig_s=go.Figure()
            fig_s.add_trace(go.Scatter(x=non_cfp["Power_Index"],y=non_cfp["Net_PPG"],
                mode="markers",marker=dict(color=GRAY,size=5,opacity=0.35),
                name="Other FBS",hovertemplate="%{text}<extra></extra>",text=non_cfp["School"]))
            fig_s.add_trace(go.Scatter(x=cfp_df["Power_Index"],y=cfp_df["Net_PPG"],
                mode="markers+text",text=cfp_df["School"],textposition="top right",
                textfont=dict(size=9,color=GOLD),
                marker=dict(color=GOLD,size=12,line=dict(width=1.5,color="#0a0d1a")),
                name="CFP Teams",hovertemplate="<b>%{text}</b><br>PI: %{x:.3f}<br>Net PPG: %{y:.1f}<extra></extra>"))
            fig_s.update_layout(**PL,title="Power Index vs Net PPG",
                xaxis_title="Power Index",yaxis_title="Net PPG",height=400,
                legend=dict(x=0.02,y=0.98,bgcolor="rgba(0,0,0,0)"),
                margin=dict(l=20,r=20,t=45,b=20))
            fig_s.add_hline(y=0,line_dash="dash",line_color="#252850")
            fig_s.add_vline(x=0,line_dash="dash",line_color="#252850")
            sf(fig_s); st.plotly_chart(fig_s,use_container_width=True)

        # Seed vs Power Rank scatter
        with col2:
            st.markdown("#### CFP Seed vs. Power Index Rank")
            cfp_data=v1[v1["Made_CFP"]==1].copy()
            cfp_data["CFP_Seed"]=cfp_data["School"].map(CFP_SEEDS)
            cfp_data["Diff"]=cfp_data["CFP_Seed"]-cfp_data["Power_Rank"]
            fig_sv=go.Figure()
            cfp_data_sorted=cfp_data.sort_values("Power_Rank")
            dot_colors=[GREEN if d>=0 else RED for d in cfp_data_sorted["Diff"]]
            fig_sv.add_trace(go.Scatter(
                x=cfp_data_sorted["Power_Rank"],y=cfp_data_sorted["CFP_Seed"],
                mode="markers+text",text=cfp_data_sorted["School"],
                textposition="top right",textfont=dict(size=9,color="#b0b4c8"),
                marker=dict(color=dot_colors,size=12,line=dict(width=1.5,color="#0a0d1a")),
                hovertemplate="<b>%{text}</b><br>Power Rank: #%{x}<br>CFP Seed: #%{y}<extra></extra>"))
            fig_sv.add_trace(go.Scatter(x=[0,90],y=[0,13],mode="lines",
                line=dict(dash="dash",color="#252850"),showlegend=False))
            fig_sv.update_layout(**PL,title="CFP Seed vs Power Rank",
                xaxis_title="Power Index Rank",yaxis_title="CFP Seed",
                yaxis=dict(autorange="reversed"),height=400,showlegend=False,
                margin=dict(l=20,r=20,t=45,b=20))
            sf(fig_sv); st.plotly_chart(fig_sv,use_container_width=True)

        # Bracket Retrodiction
        st.markdown("#### Bracket Predictions — Retrodiction")
        rc={"First Round":BLUE,"Quarterfinal":GOLD,"Semifinal":RED,"Championship":GREEN}
        for rnd,a,b,actual,correct_g,conf in BRACKET:
            icon="✅" if correct_g else "❌"
            bg="rgba(110,200,122,.04)" if correct_g else "rgba(224,82,82,.06)"
            bc=f"rgba(110,200,122,.15)" if correct_g else "rgba(224,82,82,.2)"
            rcolor=rc.get(rnd,GOLD)
            st.markdown(f"""<div style="display:grid;grid-template-columns:110px 1fr 120px 80px 50px;
                gap:12px;align-items:center;background:{bg};border:1px solid {bc};
                border-left:3px solid {rcolor};border-radius:6px;padding:10px 14px;margin-bottom:6px">
                <span style="font-size:.75rem;color:{rcolor};font-weight:700;text-transform:uppercase">{rnd}</span>
                <span style="font-size:.88rem;color:#c8cbd8"><b style="color:#eae7e0">{a}</b> <span style="color:#3a3e5a">vs</span> <b style="color:#eae7e0">{b}</b></span>
                <span style="font-size:.8rem;color:#7a7ea8">Model: {a if conf>50 else b} ({conf}%)</span>
                <span style="font-size:.8rem;color:#eae7e0;font-weight:600">✓ {actual}</span>
                <span style="font-size:1.1rem;text-align:center">{icon}</span>
            </div>""",unsafe_allow_html=True)

        st.markdown('<div class="note"><strong>Both misses were coin-flips</strong> — Ohio State vs Miami (FL) at 55.6% and Ole Miss vs Miami (FL) at 55.7%. The model nailed every lopsided matchup and the champion.</div>',unsafe_allow_html=True)

        # CFP comparison table
        st.markdown("#### Power Index vs Committee — Full CFP Field")
        if has_v1:
            cfp_tbl=v1[v1["Made_CFP"]==1][["School","Power_Rank","Power_Index","Off_PPG","Def_PPG_Allowed","Net_PPG"]].copy()
            cfp_tbl["CFP_Seed"]=cfp_tbl["School"].map(CFP_SEEDS)
            cfp_tbl["Δ Seed−Rank"]=cfp_tbl["CFP_Seed"]-cfp_tbl["Power_Rank"]
            cfp_tbl=cfp_tbl.sort_values("CFP_Seed").reset_index(drop=True)
            cfp_tbl.columns=["School","Power Rank","Power Index","Off PPG","Def PPG","Net PPG","CFP Seed","Δ Seed−Rank"]
            st.dataframe(cfp_tbl.style.format({"Power Index":"{:.3f}","Off PPG":"{:.1f}","Def PPG":"{:.1f}","Net PPG":"{:.1f}","Δ Seed−Rank":"{:+.0f}"}),
                use_container_width=True,hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4: GAME PREDICTOR
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("### ⚔️ Game Predictor")
    mode=st.radio("Model basis",["2026 V2 (preseason)","2025 V1 (historical)"],horizontal=True,key="pred_mode")
    use_v2_pred = (mode=="2026 V2 (preseason)") and has_v2
    use_v1_pred = (mode=="2025 V1 (historical)") and has_v1
    pred_teams = v2.sort_values("rank_v2")["School"].tolist() if use_v2_pred else (v1.sort_values("Power_Rank")["School"].tolist() if use_v1_pred else teams_sorted)

    c1,c2,c3=st.columns([2,1,2])
    with c1: ta=st.selectbox("Team A",pred_teams,index=0,key="gpa")
    with c2: venue=st.radio("Venue",["Neutral",f"{ta.split()[0]} home","Away"],key="gpv")
    with c3: tb=st.selectbox("Team B",pred_teams,index=2,key="gpb")

    w1,w2,w3=st.columns(3)
    with w1: wind=st.slider("Wind (mph)",0,40,0,key="wind")
    with w2: precip=st.checkbox("Precipitation",key="precip")
    with w3: cold=st.checkbox("Cold (<35°F)",key="cold")

    pow_v={"Michigan","Penn State","Ohio State","Tennessee","Texas A&M","Alabama","LSU","Texas","Georgia"}

    if use_v2_pred:
        ra=v2[v2["School"]==ta].iloc[0]; rb=v2[v2["School"]==tb].iloc[0]
        pa=ra["power_index_v2"]; pb=rb["power_index_v2"]
        qa=QB_2026.get(to_v1_name(ta),{}).get("score",50); qbs=QB_2026.get(to_v1_name(tb),{}).get("score",50)
        pa_adj=pa+(qa-65)*0.08; pb_adj=pb+(qbs-65)*0.08
        hfa=0.0
        if "home" in venue: hfa=4.0 if ta in pow_v else 2.5
        elif "Away" in venue: hfa=-(4.0 if tb in pow_v else 2.5)
        wx=0.0
        if wind>=20: wx+=(wind-15)*0.12
        if precip: wx+=1.2
        if cold: wx+=0.8
        qa_ypa=QB_2026.get(to_v1_name(ta),{}).get("ypa",7.5); qb_ypa=QB_2026.get(to_v1_name(tb),{}).get("ypa",7.5)
        if qa_ypa>qb_ypa: pa_adj-=wx
        else: pb_adj-=wx
        k=0.1; prob_a=1/(1+np.exp(-k*((pa_adj-pb_adj)+hfa)))
        margin=(pa_adj-pb_adj+hfa)*0.38
        qb_a_name=QB_2026.get(to_v1_name(ta),{}).get("qb","?"); qb_b_name=QB_2026.get(to_v1_name(tb),{}).get("qb","?")
    elif use_v1_pred:
        ra=v1[v1["School"]==ta].iloc[0]; rb=v1[v1["School"]==tb].iloc[0]
        pa=ra["Power_Index"]; pb=rb["Power_Index"]
        hfa=0.0
        if "home" in venue: hfa=0.4 if ta in pow_v else 0.3
        elif "Away" in venue: hfa=-(0.4 if tb in pow_v else 0.3)
        k=1.2; prob_a=1/(1+np.exp(-k*((pa-pb)+hfa)))
        margin=(pa-pb+hfa)*15
        pa_adj=pa; pb_adj=pb
        qb_a_name="—"; qb_b_name="—"
    else:
        st.error("No model data available."); st.stop()

    fav=ta if prob_a>0.5 else tb
    proj_a=max(14,round(21+margin/2)); proj_b=max(7,round(21-margin/2))

    m1,m2,m3=st.columns(3)
    with m1: st.markdown(f'<div class="kpi"><div class="lbl">{ta}</div><div class="val">{prob_a*100:.1f}%</div><div class="sub">QB: {qb_a_name}</div></div>',unsafe_allow_html=True)
    with m2: st.markdown(f'<div class="kpi"><div class="lbl">Projected</div><div class="val">{proj_a} – {proj_b}</div><div class="sub">{fav} by ~{abs(margin):.1f}</div></div>',unsafe_allow_html=True)
    with m3: st.markdown(f'<div class="kpi"><div class="lbl">{tb}</div><div class="val">{(1-prob_a)*100:.1f}%</div><div class="sub">QB: {qb_b_name}</div></div>',unsafe_allow_html=True)

    fp=go.Figure()
    fp.add_trace(go.Bar(y=["Win Prob"],x=[prob_a*100],orientation="h",marker_color=BLUE,name=ta,text=f"{prob_a*100:.0f}%",textposition="inside",textfont=dict(size=15,color="white")))
    fp.add_trace(go.Bar(y=["Win Prob"],x=[(1-prob_a)*100],orientation="h",marker_color=RED,name=tb,text=f"{(1-prob_a)*100:.0f}%",textposition="inside",textfont=dict(size=15,color="white")))
    fp.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(10,13,26,.85)",
        barmode="stack",height=90,xaxis=dict(visible=False),yaxis=dict(visible=False),
        margin=dict(l=0,r=0,t=0,b=0),
        legend=dict(orientation="h",x=0.5,xanchor="center",y=-0.5,font=dict(color="#b0b4c8")))
    st.plotly_chart(fp,use_container_width=True)

    # Component radar
    if use_v2_pred:
        cats=[c[1] for c in COMPONENTS if c[0] in v2.columns]
        va=[gc(ra,c[0]) for c in COMPONENTS if c[0] in v2.columns]
        vb=[gc(rb,c[0]) for c in COMPONENTS if c[0] in v2.columns]
        cats_c=cats+[cats[0]]
        frd=go.Figure()
        frd.add_trace(go.Scatterpolar(r=va+[va[0]],theta=cats_c,fill="toself",name=ta,line_color=BLUE,fillcolor="rgba(74,126,237,.2)"))
        frd.add_trace(go.Scatterpolar(r=vb+[vb[0]],theta=cats_c,fill="toself",name=tb,line_color=RED,fillcolor="rgba(224,82,82,.15)"))
        frd.update_layout(**PL,height=380,
            polar=dict(bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(visible=True,range=[0,100],gridcolor="#161a2e",tickfont=dict(size=8,color="#4a4e6a")),
                angularaxis=dict(gridcolor="#1e2240",tickfont=dict(size=9,color="#b0b4c8"))),
            legend=dict(orientation="h",x=0.5,xanchor="center",y=-0.1))
        st.plotly_chart(frd,use_container_width=True)

    # QB Assigner (V2 only)
    if use_v2_pred:
        st.markdown("---")
        st.markdown("### 🎯 Interactive QB Assigner")
        st.markdown("_What if a different QB suited up? Drag any portal QB to either team._")
        all_qbs=[(q["qb"],s,q.get("score",50)) for s,q in QB_2026.items() if q.get("qb","TBD")!="TBD"]
        qb_opts=[f"{n} ({sc}, score={s})" for n,sc,s in all_qbs]
        qa2,qb2=st.columns(2)
        with qa2:
            sela=st.selectbox(f"Hypothetical QB for {ta}",["Use current"]+qb_opts,key="ha")
            hsa=qa
            if sela!="Use current":
                m=re.search(r"score=(\d+)",sela)
                if m: hsa=int(m.group(1))
        with qb2:
            selb=st.selectbox(f"Hypothetical QB for {tb}",["Use current"]+qb_opts,key="hb")
            hsb=qbs
            if selb!="Use current":
                m=re.search(r"score=(\d+)",selb)
                if m: hsb=int(m.group(1))
        if sela!="Use current" or selb!="Use current":
            pah=pa+(hsa-65)*0.08; pbh=pb+(hsb-65)*0.08
            probh=1/(1+np.exp(-k*((pah-pbh)+hfa)))
            diff=(probh-prob_a)*100
            st.markdown(f'<div class="note"><strong>Hypothetical:</strong> With swapped QBs, {ta} win probability → <b>{probh*100:.1f}%</b> (base: {prob_a*100:.1f}%) — a <b>{diff:+.1f}pp</b> shift.</div>',unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5: PORTAL LAB
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown("### 🔬 Transfer Portal Lab — 2026")
    tf=st.multiselect("Tiers",["Elite","Proven","Raw"],default=["Elite","Proven","Raw"],key="tf")
    pteam=st.text_input("Filter by team","",key="ptf")
    filt=[p for p in PORTAL_ELITES if p[0] in tf]
    if pteam: filt=[p for p in filt if pteam.lower() in p[4].lower() or pteam.lower() in p[3].lower()]

    if filt:
        prows=[{"Tier":t,"Player":pl,"Pos":po,"From":fr,"To":to2,"Rating":f"{rt:.2f}","2025 Production":st2,"Role":ro,"NIL Est":ni}
               for t,pl,po,fr,to2,rt,st2,ro,ni in filt]
        st.dataframe(pd.DataFrame(prows),use_container_width=True,hide_index=True,
                     height=min(650,len(prows)*40+45))

    c_pos,c_haul=st.columns(2)
    with c_haul:
        st.markdown("#### Best Receiving Programs")
        haul={}
        for t,pl,po,fr,to2,rt,*_ in PORTAL_ELITES:
            if t in("Elite","Proven"):
                haul.setdefault(to2,{"count":0,"rt":0.0,"players":[]})
                haul[to2]["count"]+=1; haul[to2]["rt"]+=rt; haul[to2]["players"].append(f"{pl}({po})")
        hdf=pd.DataFrame([{"Team":k,"Adds":v["count"],"Avg Rating":v["rt"]/v["count"],"Key Adds":"; ".join(v["players"][:2])}
                           for k,v in sorted(haul.items(),key=lambda x:-x[1]["count"])])
        if not hdf.empty:
            st.dataframe(hdf.style.format({"Avg Rating":"{:.3f}"}),use_container_width=True,hide_index=True)

    with c_pos:
        st.markdown("#### Raw / Upside Prospects")
        raw_p=[(pl,po,fr,to2,rt,st2) for t,pl,po,fr,to2,rt,st2,ro,ni in PORTAL_ELITES if t=="Raw"]
        if raw_p:
            rdf=pd.DataFrame([{"Player":pl,"Pos":po,"From":fr,"To":to2,"Rating":f"{rt:.2f}","Stat Context":st2}
                              for pl,po,fr,to2,rt,st2 in raw_p])
            st.dataframe(rdf,use_container_width=True,hide_index=True)

    st.markdown("#### All Verified 2026 QB Situations")
    qbrows=[]
    for s,q in sorted(QB_2026.items()):
        tr=v2[v2["School"]==to_v2_name(s)] if has_v2 else pd.DataFrame()
        rk=int(tr["rank_v2"].iloc[0]) if not tr.empty else 999
        qbrows.append({"Rank":rk,"Team":s,"QB":q["qb"],"Type":q["type"],
            "2025 Yds":q["yds"] if q["yds"]>0 else "—","TD":q["td"] if q["td"]>0 else "—",
            "INT":q["int"] if q["int"]>0 else "—","Score":q["score"]})
    st.dataframe(pd.DataFrame(qbrows).sort_values("Rank"),use_container_width=True,hide_index=True,height=480)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6: METHODOLOGY
# ══════════════════════════════════════════════════════════════════════════════
with tab6:
    c1,c2=st.columns(2)
    with c1:
        st.markdown("### V1 — 2025 Efficiency Index")
        st.markdown("""
Six per-play efficiency metrics, z-score standardized, weighted into a composite:

| Metric | Formula | Weight |
|--------|---------|--------|
| Off Efficiency | PPG ÷ Plays/Game | 30% |
| Explosive Score | Yds/Play × Off Eff | 20% |
| Def Efficiency | PPG Allowed ÷ Plays | −25% |
| Havoc Rate | Takeaways ÷ Plays | 10% |
| Net PPG | Off − Def PPG | 10% |
| Net Yds/Game | Off − Def Yds | 5% |

**Win probability:** `P(A) = 1/(1+e^{-k(PI_A − PI_B + HFA)})` where k=1.2, HFA=0.3–0.4.

Validated: **9/11 CFP bracket games** predicted correctly. Captured **6/12 CFP teams** in top 12 (vs 4/12 for raw offense rank).
        """)

        st.markdown("### V2 — 2026 Forward-Looking Index")
        st.markdown("""
Eight components, each 0–100, weighted composite. QB now uses verified 2026 starter data.

| Component | Weight |
|-----------|--------|
| Prior-Year Quality | 35% |
| Returning Production | 20% |
| QB Room | 12% |
| Transfer Impact | 10% |
| Recruiting/Talent | 8% |
| Coaching Continuity | 7% |
| Schedule Strength | 5% |
| Context | 3% |

Transfer QBs discounted 5–8% for first-year system adjustment. Missing data defaults to neutral 50/100.
        """)

    with c2:
        st.markdown("### Data Files Status")
        files=[
            ("cfb_combined_data.xlsx","2025 base stats (V1)","Required"),
            ("cfb_power_index_v2.csv","V2 model output","Run model_v2.py"),
            ("data/raw/2026_returning_production.csv","Returning production","Important"),
            ("data/raw/2026_coaches.csv","Coaching continuity","Important"),
            ("data/raw/2022_2026_recruiting.csv","Recruiting talent","Important"),
            ("data/raw/2026_schedule.csv","Schedule strength","Important"),
            ("data/raw/2026_transfers.csv","Transfer detail","Nice-to-have"),
        ]
        frows=[{"File":os.path.basename(f),"Feeds":d,"Status":"✅" if os.path.exists(f) else "⬜","Priority":p}
               for f,d,p in files]
        st.dataframe(pd.DataFrame(frows),use_container_width=True,hide_index=True)

        st.markdown("#### QB Data (hardcoded, June 2026)")
        st.markdown(f"""
- **{sum(1 for q in QB_2026.values() if q['type']=='returning')}** verified returning starters
- **{sum(1 for q in QB_2026.values() if q['type']=='transfer')}** verified transfer starters (real 2025 stats)
- **{sum(1 for q in QB_2026.values() if q['type'] in ('battle','unknown','freshman'))}** open battles / unknowns
- Key corrections: Arch Manning ✅ Texas, Dante Moore ✅ Oregon, Bryce Underwood ✅ Michigan, Sam Leavitt ✅ LSU, Rocco Becht ✅ Penn State
        """)

    st.markdown("---")
    st.markdown('<small style="color:#4a4e6a">CFB Power Index · Andrew White · MSBA, UT Austin McCombs · Not affiliated with ESPN, 247Sports, or NCAA</small>',unsafe_allow_html=True)
