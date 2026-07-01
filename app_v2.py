"""
CFB Power Index V2 — app_v2.py
Updated June 2026 with verified QB situations, portal player tiers,
interactive QB assigner, 5-tab structure, Top 10 cards.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os, re

st.set_page_config(page_title="CFB Power Index V2", page_icon="🏈",
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
.stTabs [data-baseweb="tab-list"]{gap:6px;border-bottom:1px solid #1e2240}
.stTabs [data-baseweb="tab"]{background:transparent;color:#7a7ea8;border-radius:8px 8px 0 0;padding:10px 22px;font-weight:600;font-size:.9rem}
.stTabs [aria-selected="true"]{background:#c8aa6e!important;color:#0a0d1a!important}
div[data-testid="stMetric"]{background:#111428;border:1px solid #1e2240;border-radius:10px;padding:14px 18px}
div[data-testid="stMetric"] label{color:#8a8ea8!important;font-size:.75rem!important;text-transform:uppercase;letter-spacing:1px}
div[data-testid="stMetric"] [data-testid="stMetricValue"]{color:#c8aa6e!important;font-family:'Playfair Display',serif!important}
</style>
""", unsafe_allow_html=True)

# ─── Verified 2026 QB Data ────────────────────────────────────────────────────
QB_2026 = {
    "Ohio State":    {"qb":"Julian Sayin",    "type":"returning","yds":3610,"td":32,"int":8,"cmp":77.0,"ypa":9.2,"score":92},
    "Texas":         {"qb":"Arch Manning",    "type":"returning","yds":3163,"td":26,"int":7,"cmp":72.0,"ypa":8.8,"score":88},
    "Ole Miss":      {"qb":"T. Chambliss",   "type":"returning","yds":3937,"td":22,"int":3,"cmp":66.1,"ypa":8.9,"score":86},
    "Georgia":       {"qb":"Gunner Stockton", "type":"returning","yds":2894,"td":24,"int":5,"cmp":64.0,"ypa":8.2,"score":84},
    "Miami (FL)":    {"qb":"Darian Mensah",   "type":"transfer","yds":3973,"td":34,"int":6,"cmp":66.8,"ypa":9.1,"score":83},
    "Notre Dame":    {"qb":"CJ Carr",         "type":"returning","yds":2741,"td":24,"int":6,"cmp":66.6,"ypa":9.4,"score":82},
    "Oklahoma State":{"qb":"Drew Mestemaker", "type":"transfer","yds":4379,"td":34,"int":9,"cmp":68.9,"ypa":9.5,"score":82},
    "Oregon":        {"qb":"Dante Moore",     "type":"returning","yds":3565,"td":30,"int":10,"cmp":71.8,"ypa":8.5,"score":80},
    "LSU":           {"qb":"Sam Leavitt",     "type":"transfer","yds":1628,"td":10,"int":3,"cmp":60.7,"ypa":8.1,"score":78},
    "Penn State":    {"qb":"Rocco Becht",     "type":"transfer","yds":2584,"td":16,"int":9,"cmp":64.0,"ypa":7.8,"score":76},
    "Auburn":        {"qb":"Byrum Brown",     "type":"transfer","yds":3158,"td":28,"int":7,"cmp":66.3,"ypa":8.4,"score":77},
    "USC":           {"qb":"Jayden Maiava",   "type":"returning","yds":3711,"td":24,"int":10,"cmp":65.8,"ypa":8.0,"score":74},
    "Nebraska":      {"qb":"A. Colandrea",    "type":"transfer","yds":3459,"td":23,"int":9,"cmp":65.9,"ypa":8.4,"score":74},
    "Vanderbilt":    {"qb":"Diego Pavia",     "type":"returning","yds":3192,"td":27,"int":8,"cmp":65.0,"ypa":8.2,"score":72},
    "Michigan":      {"qb":"Bryce Underwood", "type":"returning","yds":2428,"td":11,"int":9,"cmp":65.0,"ypa":7.4,"score":72},
    "Indiana":       {"qb":"Josh Hoover",     "type":"transfer","yds":3472,"td":29,"int":13,"cmp":65.9,"ypa":8.1,"score":72},
    "Texas A&M":     {"qb":"Marcel Reed",     "type":"returning","yds":3169,"td":25,"int":12,"cmp":62.1,"ypa":7.6,"score":70},
    "South Carolina":{"qb":"LaNorris Sellers","type":"returning","yds":2437,"td":13,"int":8,"cmp":60.8,"ypa":7.4,"score":68},
    "Oklahoma":      {"qb":"John Mateer",     "type":"returning","yds":2885,"td":14,"int":11,"cmp":62.2,"ypa":7.2,"score":66},
    "Arizona State": {"qb":"Cutter Boley",    "type":"transfer","yds":2160,"td":15,"int":12,"cmp":65.8,"ypa":7.5,"score":64},
    "Tennessee":     {"qb":"TBD (open battle)","type":"battle", "yds":0,"td":0,"int":0,"cmp":0,"ypa":0,"score":55},
    "Alabama":       {"qb":"Mack vs Russell", "type":"battle",  "yds":0,"td":0,"int":0,"cmp":0,"ypa":0,"score":52},
    "Clemson":       {"qb":"TBD (Klubnik gone)","type":"battle","yds":0,"td":0,"int":0,"cmp":0,"ypa":0,"score":48},
    "Florida":       {"qb":"T. Jones Jr. (FR)","type":"freshman","yds":0,"td":0,"int":0,"cmp":0,"ypa":0,"score":45},
    "Texas Tech":    {"qb":"Sorsby (risk)",   "type":"battle",  "yds":0,"td":0,"int":0,"cmp":0,"ypa":0,"score":50},
}

PORTAL_ELITES = [
    ("Elite",  "Sam Leavitt",      "QB",    "Arizona State","LSU",            0.99,"4,652 career yds / 36 TD","Career","Day-1 Starter","$4M+"),
    ("Elite",  "Cam Coleman",      "WR",    "Auburn",       "Texas",          0.97,"708 yds / 5 TD (2025)",   "Season","Day-1 Starter","$3M+"),
    ("Elite",  "Drew Mestemaker",  "QB",    "North Texas",  "Oklahoma State", 0.97,"4,379 yds / 34 TD (led FBS)","Season","Day-1 Starter","$7M/2yr"),
    ("Elite",  "Darian Mensah",    "QB",    "Duke",         "Miami (FL)",     0.96,"3,973 yds / 34 TD / 6 INT","Season","Day-1 Starter","$10M"),
    ("Elite",  "Rocco Becht",      "QB",    "Iowa State",   "Penn State",     0.95,"9,275 career yds / 64 TD", "Career","Day-1 Starter","N/A"),
    ("Elite",  "Byrum Brown",      "QB",    "South Florida","Auburn",         0.94,"3,158 yds / 28 TD + 1,008 rush","Season","Day-1 Starter","N/A"),
    ("Elite",  "JJ Buchanan",      "WR/TE", "Utah",         "Michigan",       0.94,"427 yds / 5 TD (FR 2025)","Season","Top-3 WR","N/A"),
    ("Proven", "A. Colandrea",     "QB",    "UNLV",         "Nebraska",       0.88,"3,459 yds / 23 TD (MW leader)","Season","Day-1 Starter","N/A"),
    ("Proven", "Josh Hoover",      "QB",    "TCU",          "Indiana",        0.86,"3,472 yds / 29 TD / 13 INT","Season","Day-1 Starter","N/A"),
    ("Proven", "Cutter Boley",     "QB",    "Kentucky",     "Arizona State",  0.85,"2,160 yds / 15 TD (2025)","Season","Battle","N/A"),
    ("Proven", "J.H. Daley",       "EDGE",  "Utah",         "Michigan",       0.90,"10.5 TFL / 7.5 sacks (2025)","Season","Day-1 Starter","N/A"),
    ("Proven", "Dylan Raiola",     "QB",    "Nebraska",     "Oregon",         0.90,"2025 Nebraska starter","Season","Backup/RS","N/A"),
    ("Raw",    "Lance Heard",      "OT",    "Tennessee",    "Kentucky",       0.87,"2025 SEC blocker","Role","Starter","N/A"),
    ("Raw",    "Nick Marsh",       "WR",    "Michigan State","Indiana",       0.86,"733 yds / 6 TD (2025)","Season","Starter","N/A"),
    ("Raw",    "James Smith",      "DL",    "Alabama",      "Ohio State",     0.88,"6.5 sacks (2025)","Season","Rotational","N/A"),
    ("Raw",    "Koi Perich",       "S",     "Minnesota",    "Oregon",         0.88,"5 INT / 78 tackles (2025)","Season","Starter","N/A"),
    ("Raw",    "Tionne Gray",      "DL",    "Oregon",       "Notre Dame",     0.87,"2025 Pac-12 DL","Role","Rotational","N/A"),
    ("Raw",    "Terrell Anderson", "WR",    "NC State",     "USC",            0.85,"2025 ACC WR","Role","Rotational","N/A"),
    ("Raw",    "Jontez Williams",  "CB",    "Iowa State",   "USC",            0.86,"3 INT (2025)","Season","Starter","N/A"),
]

GOLD="#c8aa6e"; BLUE="#4a7eed"; RED="#e05252"; GREEN="#6ec87a"; GRAY="#3a3e5a"
PL=dict(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(10,13,26,.85)",
        font=dict(family="Inter,sans-serif",color="#b0b4c8"),
        title_font=dict(family="Playfair Display,serif",color="#eae7e0",size=17),
        hoverlabel=dict(bgcolor="#161830",bordercolor="#c8aa6e",font_color="#e8e0d0"),
        margin=dict(l=10,r=10,t=45,b=10))
AX=dict(gridcolor="#161a2e",zerolinecolor="#1e2240")
def sf(f): f.update_xaxes(**AX); f.update_yaxes(**AX); return f

@st.cache_data
def load():
    for p in ["cfb_power_index_v2.csv","data/processed/cfb_power_index_v2.csv"]:
        if os.path.exists(p): return pd.read_csv(p)
    return pd.DataFrame()

@st.cache_data
def load_sched():
    for p in ["data/raw/2026_schedule.csv","2026_schedule.csv"]:
        if os.path.exists(p): return pd.read_csv(p)
    return pd.DataFrame()

df=load(); sched_df=load_sched()

# Normalize column name: some model versions use 'team' instead of 'School'
if not df.empty and "School" not in df.columns:
    for alt in ["team","Team","school"]:
        if alt in df.columns:
            df = df.rename(columns={alt: "School"})
            break

# Normalize rank/delta columns
if "rank_v2" not in df.columns:
    for alt in ["Rank_2026","power_rank_v2"]:
        if alt in df.columns: df=df.rename(columns={alt:"rank_v2"}); break
if "delta_vs_2025" not in df.columns:
    df["delta_vs_2025"] = 0
if "Rank_2025" not in df.columns:
    df["Rank_2025"] = df.get("rank_v2", pd.Series(range(1,len(df)+1)))

COMPONENTS=[
    ("prior_year_team_quality_score","Prior-Year Quality",35),
    ("returning_production_score","Returning Production",20),
    ("qb_score","QB Room",12),
    ("transfer_impact_score","Transfer Impact",10),
    ("recruiting_talent_score","Recruiting/Talent",8),
    ("coaching_continuity_score","Coaching",7),
    ("schedule_strength_score","Schedule Strength",5),
    ("context_score","Context",3),
]

def gc(row,col,d=50):
    return float(row[col]) if col in df.columns and pd.notna(row.get(col)) else d

st.markdown("""
<div class="hero">
  <h1>🏈 CFB Power Index V2</h1>
  <p>Roster-aware 2026 preseason model · Verified QB situations · Real portal data · Schedule strength · Game predictor</p>
</div>""", unsafe_allow_html=True)

if df.empty:
    st.error("Run `python model_v2.py` first to generate `cfb_power_index_v2.csv`.")
    st.stop()

df["qb_name"]=df["School"].map(lambda s:QB_2026.get(s,{}).get("qb","Unknown"))
df["qb_type"]=df["School"].map(lambda s:QB_2026.get(s,{}).get("type","unknown"))
teams_sorted=df.sort_values("rank_v2")["School"].tolist()

tab1,tab2,tab3,tab4,tab5=st.tabs(["📊 Rankings","🔍 Team Intel","⚔️ Game Predictor","🔬 Portal Lab","📐 About"])

# ════════════════════════ TAB 1: RANKINGS ════════════════════════
with tab1:
    f1,f2,f3,f4=st.columns([2,2,2,1])
    with f1:
        conf_opts=["All"]+sorted(df["conference"].dropna().unique().tolist()) if "conference" in df.columns else ["All"]
        conf_f=st.selectbox("Conference",conf_opts,key="cf")
    with f2: move_f=st.selectbox("Movement",["All","Risers (↑5+)","Fallers (↓5+)","Stable"],key="mf")
    with f3: qb_f=st.selectbox("QB Status",["All","Returning","Transfer","Battle"],key="qf")
    with f4: top_n=st.selectbox("Show",[10,15,25,50,len(df)],index=2,key="rn")

    disp=df.copy()
    if conf_f!="All" and "conference" in df.columns: disp=disp[disp["conference"]==conf_f]
    if move_f=="Risers (↑5+)": disp=disp[disp["delta_vs_2025"]>=5]
    elif move_f=="Fallers (↓5+)": disp=disp[disp["delta_vs_2025"]<=-5]
    elif move_f=="Stable": disp=disp[disp["delta_vs_2025"].abs()<5]
    if qb_f=="Returning": disp=disp[disp["qb_type"]=="returning"]
    elif qb_f=="Transfer": disp=disp[disp["qb_type"]=="transfer"]
    elif qb_f=="Battle": disp=disp[disp["qb_type"].isin(["battle","unknown","freshman"])]
    disp=disp.sort_values("rank_v2").head(top_n)

    st.markdown("#### Top 10")
    top10=df.sort_values("rank_v2").head(10)
    cols=st.columns(10)
    for i,(_,r) in enumerate(top10.iterrows()):
        d=int(r.get("delta_vs_2025",0))
        dc="#6ec87a" if d>0 else ("#e05252" if d<0 else "#5a5e7a")
        ds=f"↑{d}" if d>0 else (f"↓{abs(d)}" if d<0 else "—")
        qn=r.get("qb_name","?"); qs=qn[:12]+"…" if len(qn)>13 else qn
        cols[i].markdown(f"""<div class="top10-card">
          <div class="rnk">#{int(r['rank_v2'])}</div>
          <div class="team">{r['School']}</div>
          <div class="idx">{r['power_index_v2']:.1f}</div>
          <div class="delta" style="color:{dc}">{ds}</div>
          <div class="qb">{qs}</div>
        </div>""", unsafe_allow_html=True)

    st.write("")
    colors=[GREEN if d>2 else (RED if d<-2 else GOLD) for d in disp["delta_vs_2025"]]
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
    st.markdown('<span style="font-size:.78rem;color:#5a5e7a">🟢 Riser +5  🟡 Stable  🔴 Faller −5</span>',unsafe_allow_html=True)

    st.markdown("#### Why does a team rank here?")
    et=st.selectbox("Select team",teams_sorted,key="et")
    er=df[df["School"]==et].iloc[0]
    s2=sorted([(c[1],gc(er,c[0])) for c in COMPONENTS],key=lambda x:-x[1])
    t3=[s for s in s2 if s[1]>=65][:3]; w2=[s for s in s2 if s[1]<52][:2]
    qbi=QB_2026.get(et,{})
    msg=f"**{et}** ranks **#{int(er['rank_v2'])}** (was #{int(er['Rank_2025'])}, Δ{int(er['delta_vs_2025']):+d}). "
    if t3: msg+="Strengths: "+", ".join(f"**{n}** ({v:.0f})" for n,v in t3)+". "
    if w2: msg+="Drags: "+", ".join(f"{n} ({v:.0f})" for n,v in w2)+". "
    qt=qbi.get("type","unknown")
    if qt=="returning": msg+=f"QB **{qbi.get('qb','?')}** returns (score {qbi.get('score',50)})."
    elif qt=="transfer": msg+=f"Transfer QB **{qbi.get('qb','?')}** (score {qbi.get('score',50)}, system-adj discount applied)."
    else: msg+="⚠️ QB situation unresolved — highest model uncertainty."
    st.markdown(f'<div class="note">{msg}</div>',unsafe_allow_html=True)

    st.markdown("#### Full Rankings Table")
    show=["rank_v2","School","power_index_v2","Rank_2025","delta_vs_2025","qb_name","qb_type"]
    show=[c for c in show if c in df.columns or c in ["qb_name","qb_type"]]
    tbl=disp[show].copy()
    tbl.columns=["Rank","Team","PI V2","2025","Δ","QB","QB Type"]
    tbl["Δ"]=tbl["Δ"].apply(lambda x:f"{int(x):+d}")
    st.dataframe(tbl.style.format({"PI V2":"{:.1f}"}),use_container_width=True,
                 hide_index=True,height=min(900,len(tbl)*38+40))

# ════════════════════════ TAB 2: TEAM INTEL ════════════════════════
with tab2:
    team=st.selectbox("Select team",teams_sorted,key="ti")
    r=df[df["School"]==team].iloc[0]; qbi=QB_2026.get(team,{})

    k1,k2,k3,k4,k5=st.columns(5)
    with k1: st.metric("V2 Rank",f"#{int(r['rank_v2'])}")
    with k2: st.metric("Power Index",f"{r['power_index_v2']:.1f}")
    with k3: st.metric("2025 Rank",f"#{int(r['Rank_2025'])}")
    with k4:
        d=int(r["delta_vs_2025"])
        st.metric("Movement",f"{d:+d}",delta="Riser" if d>0 else ("Faller" if d<0 else "Stable"))
    with k5:
        sos=gc(r,"schedule_strength_score")
        st.metric("SOS Score",f"{sos:.0f}/100")

    st.markdown("#### QB Room — 2026")
    qt=qbi.get("type","unknown")
    qtype_lbl={"returning":"✅ Returning Starter","transfer":"🔄 Transfer Starter",
                "battle":"⚠️ Open Battle","freshman":"🆕 Freshman","unknown":"❓ Unknown"}.get(qt,"❓")
    if qbi.get("yds",0)>0:
        st.markdown(f"""<div class="kpi" style="text-align:left;padding:16px 20px">
          <div style="font-size:1.1rem;font-weight:700;color:#eae7e0;margin-bottom:8px">
            {qbi.get('qb','?')} &nbsp;<span style="font-size:.78rem;color:#7a7ea8">{qtype_lbl}</span>
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
        st.markdown(f'<div class="note"><strong>{qbi.get("qb","?")}</strong> — {qtype_lbl}. No stats available (open competition or freshman).</div>',unsafe_allow_html=True)

    st.write("")
    cr,cb=st.columns(2)
    cats=[c[1] for c in COMPONENTS if c[0] in df.columns]
    vals=[gc(r,c[0]) for c in COMPONENTS if c[0] in df.columns]
    with cr:
        st.markdown("#### Efficiency Radar")
        cc=cats+[cats[0]]; vc=vals+[vals[0]]
        fr=go.Figure()
        fr.add_trace(go.Scatterpolar(r=vc,theta=cc,fill="toself",
            line_color=GOLD,fillcolor="rgba(200,170,110,.18)",name=team))
        fr.update_layout(**PL,height=370,
            polar=dict(bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(visible=True,range=[0,100],gridcolor="#161a2e",tickfont=dict(size=8,color="#4a4e6a")),
                angularaxis=dict(gridcolor="#1e2240",tickfont=dict(size=9,color="#b0b4c8"))))
        st.plotly_chart(fr,use_container_width=True)
    with cb:
        st.markdown("#### Score Breakdown")
        bc=[GREEN if v>=70 else (GOLD if v>=50 else RED) for v in vals]
        fb=go.Figure(go.Bar(y=cats,x=vals,orientation="h",marker_color=bc,
            text=[f"{v:.0f}" for v in vals],textposition="outside",textfont=dict(size=11,color="#9a9eb8")))
        fb.update_layout(**PL,height=370,xaxis=dict(range=[0,110]),
            yaxis=dict(autorange="reversed"),showlegend=False,
            margin=dict(l=130,r=40,t=30,b=20))
        sf(fb); st.plotly_chart(fb,use_container_width=True)

    s3=sorted([(c[1],gc(r,c[0])) for c in COMPONENTS],key=lambda x:-x[1])
    t3s=[s for s in s3 if s[1]>=65][:3]; w2s=[s for s in s3 if s[1]<52][:2]
    rpt=f"**{team}** ranks **#{int(r['rank_v2'])}** entering 2026 (Δ{int(r['delta_vs_2025']):+d} vs 2025). "
    if t3s: rpt+="Strengths: "+", ".join(f"**{n}** ({v:.0f})" for n,v in t3s)+". "
    if w2s: rpt+="Concerns: "+", ".join(f"{n} ({v:.0f})" for n,v in w2s)+". "
    if qt in("battle","freshman","unknown"): rpt+="⚠️ QB unresolved — highest uncertainty."
    elif qt=="transfer": rpt+=f"Transfer QB {qbi.get('qb','?')} — scheme-adjustment discount applied."
    st.markdown(f'<div class="note">{rpt}</div>',unsafe_allow_html=True)

    st.markdown("#### 2026 Portal Additions")
    tp=[p for p in PORTAL_ELITES if p[4]==team]
    if tp:
        tpdf=pd.DataFrame([{"Tier":t,"Player":pl,"Pos":po,"From":fr,"Rating":f"{rt:.2f}","2025 Stat":st2,"Role":ro,"NIL Est":ni}
                           for t,pl,po,fr,_,rt,st2,_,ro,ni in tp])
        st.dataframe(tpdf,use_container_width=True,hide_index=True)
    else:
        st.info("No verified elite/proven transfers in this team's 2026 class in the hardcoded set.")

    st.markdown("#### 2026 Schedule")
    if not sched_df.empty:
        hc="home_team" if "home_team" in sched_df.columns else "homeTeam"
        ac="away_team" if "away_team" in sched_df.columns else "awayTeam"
        if hc in sched_df.columns:
            games=sched_df[(sched_df[hc]==team)|(sched_df[ac]==team)].head(13).copy()
            games["Site"]=games.apply(lambda g:"Home" if g[hc]==team else("Neutral" if g.get("neutral_site",False) else "Away"),axis=1)
            games["Opponent"]=games.apply(lambda g:g[ac] if g[hc]==team else g[hc],axis=1)
            if "week" in games.columns: games=games.rename(columns={"week":"Wk"})
            sc=["Wk","Opponent","Site"] if "Wk" in games.columns else ["Opponent","Site"]
            st.dataframe(games[sc],use_container_width=True,hide_index=True)
    else:
        st.info("Run `python scripts/01_pull_cfbd_data.py` (with your CFBD API key) to load the 2026 schedule.")

# ════════════════════════ TAB 3: GAME PREDICTOR ════════════════════════
with tab3:
    st.markdown("### ⚔️ Head-to-Head Game Predictor")
    c1,c2,c3=st.columns([2,1,2])
    with c1: ta=st.selectbox("Team A",teams_sorted,index=0,key="gpa")
    with c2: venue=st.radio("Venue",["Neutral",f"{ta.split()[0]} home","Away"],key="gpv")
    with c3: tb=st.selectbox("Team B",teams_sorted,index=2,key="gpb")

    w1,w2,w3=st.columns(3)
    with w1: wind=st.slider("Wind (mph)",0,40,0,key="wind")
    with w2: precip=st.checkbox("Precipitation",key="precip")
    with w3: cold=st.checkbox("Cold (<35°F)",key="cold")

    ra=df[df["School"]==ta].iloc[0]; rb=df[df["School"]==tb].iloc[0]
    pa=ra["power_index_v2"]; pb=rb["power_index_v2"]
    qa=QB_2026.get(ta,{}).get("score",50); qbs=QB_2026.get(tb,{}).get("score",50)
    pa_adj=pa+(qa-65)*0.08; pb_adj=pb+(qbs-65)*0.08

    pow_v={"Michigan","Penn State","Ohio State","Tennessee","Texas A&M","Alabama","LSU","Texas","Georgia"}
    hfa=0.0
    if "home" in venue: hfa=4.0 if ta in pow_v else 2.5
    elif "Away" in venue: hfa=-(4.0 if tb in pow_v else 2.5)

    wx=0.0
    if wind>=20: wx+=(wind-15)*0.12
    if precip: wx+=1.2
    if cold: wx+=0.8
    qa_ypa=QB_2026.get(ta,{}).get("ypa",7.5); qb_ypa=QB_2026.get(tb,{}).get("ypa",7.5)
    if qa_ypa>qb_ypa: pa_adj-=wx
    else: pb_adj-=wx

    k=0.1; prob_a=1/(1+np.exp(-k*((pa_adj-pb_adj)+hfa)))
    margin=(pa_adj-pb_adj+hfa)*0.38
    fav=ta if prob_a>0.5 else tb
    proj_a=max(14,round(21+margin/2)); proj_b=max(7,round(21-margin/2))

    m1,m2,m3=st.columns(3)
    with m1: st.markdown(f'<div class="kpi"><div class="lbl">{ta}</div><div class="val">{prob_a*100:.1f}%</div><div class="sub">PI {pa:.1f} · {QB_2026.get(ta,{}).get("qb","?")}</div></div>',unsafe_allow_html=True)
    with m2: st.markdown(f'<div class="kpi"><div class="lbl">Projected</div><div class="val">{proj_a} – {proj_b}</div><div class="sub">{fav} by ~{abs(margin):.1f} pts</div></div>',unsafe_allow_html=True)
    with m3: st.markdown(f'<div class="kpi"><div class="lbl">{tb}</div><div class="val">{(1-prob_a)*100:.1f}%</div><div class="sub">PI {pb:.1f} · {QB_2026.get(tb,{}).get("qb","?")}</div></div>',unsafe_allow_html=True)

    fp=go.Figure()
    fp.add_trace(go.Bar(y=["Win Prob"],x=[prob_a*100],orientation="h",marker_color=BLUE,name=ta,text=f"{prob_a*100:.0f}%",textposition="inside",textfont=dict(size=15,color="white")))
    fp.add_trace(go.Bar(y=["Win Prob"],x=[(1-prob_a)*100],orientation="h",marker_color=RED,name=tb,text=f"{(1-prob_a)*100:.0f}%",textposition="inside",textfont=dict(size=15,color="white")))
    fp.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(10,13,26,.85)",barmode="stack",height=90,xaxis=dict(visible=False),yaxis=dict(visible=False),margin=dict(l=0,r=0,t=0,b=0),legend=dict(orientation="h",x=0.5,xanchor="center",y=-0.6,font=dict(color="#b0b4c8")))
    st.plotly_chart(fp,use_container_width=True)

    wxn="" 
    if wx>0: wxn=f" Weather: −{wx:.1f} pts to {ta if qa_ypa>qb_ypa else tb} (more pass-reliant)."
    st.markdown(f'<div class="note"><strong>Analysis:</strong> {fav} is a <b>{max(prob_a,1-prob_a)*100:.0f}%</b> favorite. QB edge: {ta} ({QB_2026.get(ta,{}).get("qb","?")} score={qa}) vs {tb} ({QB_2026.get(tb,{}).get("qb","?")} score={qbs}). HFA: {hfa:+.1f} pts.{wxn}</div>',unsafe_allow_html=True)

    st.markdown("#### Factor Breakdown")
    frows=[]
    for col,label,_ in COMPONENTS:
        if col in df.columns:
            va=gc(ra,col); vb=gc(rb,col)
            frows.append({"Factor":label,ta:f"{va:.0f}",tb:f"{vb:.0f}","Edge":ta if va>vb else tb,"Gap":f"{abs(va-vb):.0f}"})
    st.dataframe(pd.DataFrame(frows),use_container_width=True,hide_index=True)

    st.markdown("---")
    st.markdown("### 🎯 Interactive QB Assigner")
    st.markdown("_Hypothetical: try any QB at either team and see the win probability shift._")
    all_qbs=[(q["qb"],s,q["type"],q.get("score",50)) for s,q in QB_2026.items() if q.get("qb","TBD")!="TBD"]
    qb_opts=[f"{n} ({sc}, {t}, score={s})" for n,sc,t,s in all_qbs]
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

# ════════════════════════ TAB 4: PORTAL LAB ════════════════════════
with tab4:
    st.markdown("### 🔬 Transfer Portal Lab — 2026")
    tf=st.multiselect("Tiers",["Elite","Proven","Raw"],default=["Elite","Proven","Raw"],key="tf")
    pteam=st.text_input("Filter by team","",key="ptf")
    filt=[p for p in PORTAL_ELITES if p[0] in tf]
    if pteam: filt=[p for p in filt if pteam.lower() in p[4].lower() or pteam.lower() in p[3].lower()]

    if filt:
        prows=[{"Tier":t,"Player":pl,"Pos":po,"From":fr,"To":to2,"Rating":f"{rt:.2f}","2025 Production":st2,"Role":ro,"NIL Est":ni}
               for t,pl,po,fr,to2,rt,st2,_,ro,ni in filt]
        st.dataframe(pd.DataFrame(prows),use_container_width=True,hide_index=True,height=min(650,len(prows)*40+45))

    st.markdown("#### Best Receiving Programs (Elite + Proven)")
    haul={}
    for t,pl,po,fr,to2,rt,*_ in PORTAL_ELITES:
        if t in("Elite","Proven"):
            haul.setdefault(to2,{"count":0,"rt":0.0,"players":[]})
            haul[to2]["count"]+=1; haul[to2]["rt"]+=rt; haul[to2]["players"].append(f"{pl}({po})")
    hdf=pd.DataFrame([{"Team":k,"Adds":v["count"],"Avg Rating":v["rt"]/v["count"],"Key Adds":"; ".join(v["players"][:3])}
                       for k,v in sorted(haul.items(),key=lambda x:-x[1]["count"])])
    if not hdf.empty:
        st.dataframe(hdf.style.format({"Avg Rating":"{:.3f}"}),use_container_width=True,hide_index=True)

    st.markdown("#### 🎯 Raw / Unproven Prospects (Upside Targets)")
    raw_p=[(t,pl,po,fr,to2,rt,st2,ro,ni) for t,pl,po,fr,to2,rt,st2,_,ro,ni in PORTAL_ELITES if t=="Raw"]
    if raw_p:
        rdf=pd.DataFrame([{"Player":pl,"Pos":po,"From":fr,"To":to2,"Rating":f"{rt:.2f}","Stat Context":st2,"Role":ro}
                          for _,pl,po,fr,to2,rt,st2,ro,ni in raw_p])
        st.dataframe(rdf,use_container_width=True,hide_index=True)

    st.markdown("#### All 2026 QB Situations (Verified)")
    qbrows=[]
    for s,q in sorted(QB_2026.items()):
        tr=df[df["School"]==s]
        rk=int(tr["rank_v2"].iloc[0]) if not tr.empty else 999
        qbrows.append({"Rank":rk,"Team":s,"QB":q["qb"],"Type":q["type"],
            "2025 Yds":q["yds"] if q["yds"]>0 else "—","TD":q["td"] if q["td"]>0 else "—",
            "INT":q["int"] if q["int"]>0 else "—","Score":q["score"]})
    qbdf=pd.DataFrame(qbrows).sort_values("Rank")
    st.dataframe(qbdf,use_container_width=True,hide_index=True,height=500)

# ════════════════════════ TAB 5: ABOUT ════════════════════════
with tab5:
    c1,c2=st.columns(2)
    with c1:
        st.markdown("### Model Overview")
        st.markdown("""
**V2 Power Index** = weighted composite of 8 components (each 0–100):

| Component | Weight |
|---|---|
| Prior-Year Quality | 35% |
| Returning Production | 20% |
| QB Room | 12% |
| Transfer Impact | 10% |
| Recruiting/Talent | 8% |
| Coaching Continuity | 7% |
| Schedule Strength | 5% |
| Context | 3% |

**QB Room** now uses real 2026 verified starter data. Transfer QBs get a ~5–8% first-year discount.

Missing files default to neutral 50/100. Run `python model_v2.py` to rebuild after adding data.
        """)
        st.markdown("#### Key Corrections vs Old Version")
        st.markdown("""
- ✅ **Arch Manning** = Texas starter (Quinn Ewers → NFL)
- ✅ **Dante Moore** = Oregon starter (Gabriel left after 2024)  
- ✅ **Bryce Underwood** = Michigan starter under Whittingham
- ✅ **Sam Leavitt** = LSU QB under Lane Kiffin
- ✅ **Rocco Becht** = Penn State QB following Matt Campbell
        """)
    with c2:
        st.markdown("### Data Files Status")
        files=[("cfb_combined_data.xlsx","2025 base stats","Required"),
               ("data/raw/2026_returning_production.csv","Returning production","Important"),
               ("data/raw/2026_coaches.csv","Coaching continuity","Important"),
               ("data/raw/2022_2026_recruiting.csv","Recruiting talent","Important"),
               ("data/raw/2026_schedule.csv","Schedule strength","Important"),
               ("data/raw/2026_transfers.csv","Transfer detail","Nice-to-have"),
               ("data/raw/2026_qb_rooms.csv","QB rooms file","Hardcoded in app ✅")]
        frows=[{"File":os.path.basename(f),"Feeds":d,"Status":"✅" if os.path.exists(f) else "⬜","Priority":p}
               for f,d,p in files]
        st.dataframe(pd.DataFrame(frows),use_container_width=True,hide_index=True)

        st.markdown(f"""
**QB Data Summary**
- {sum(1 for q in QB_2026.values() if q['type']=='returning')} returning starters
- {sum(1 for q in QB_2026.values() if q['type']=='transfer')} transfer starters  
- {sum(1 for q in QB_2026.values() if q['type'] in ('battle','unknown','freshman'))} open battles/unknowns
        """)

    st.markdown("---")
    st.markdown('<small style="color:#4a4e6a">CFB Power Index V2 · Andrew White · MSBA, UT Austin McCombs · Not affiliated with ESPN, 247Sports, or NCAA</small>',unsafe_allow_html=True)
