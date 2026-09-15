"""
CFB Power Index — Combined V1 + V2
2025 Season Analysis + 2026 Forward-Looking Projections
Andrew White · MSBA UT Austin McCombs
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os, re, html
import live_data as L

def zscore(frame):
    """Column-wise standardization (mean 0, std 1). Returns a numpy array."""
    a = np.asarray(frame, dtype=float)
    mean = a.mean(axis=0)
    std = a.std(axis=0)
    std[std == 0] = 1.0
    return (a - mean) / std

st.set_page_config(page_title="CFB Power Index", page_icon="🏈",
                   layout="wide", initial_sidebar_state="collapsed")

# ═══════════════════════════════════════════════════════════════════════════════
# THEME
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800;900&family=Inter:wght@300;400;500;600;700;800&display=swap');
.stApp{background:radial-gradient(1200px 500px at 15% -10%,#141b3a 0%,transparent 60%),
       radial-gradient(1000px 420px at 90% 0%,#1a1430 0%,transparent 55%),#070a14;color:#d0d3e0}
section[data-testid="stSidebar"]{background:#0d1020;border-right:1px solid #1a1d30}
h1,h2,h3{font-family:'Playfair Display',serif!important;color:#eae7e0!important}
h4{color:#c8aa6e!important;font-family:'Inter',sans-serif!important;text-transform:uppercase;
   letter-spacing:1.5px;font-size:.82rem!important;font-weight:700!important}
p,li,span,div{color:#c8cbd8}
strong,b{color:#e8e5dc!important}
.stMarkdown p{color:#c8cbd8!important}

.hero{background:linear-gradient(120deg,rgba(26,31,66,.5) 0%,rgba(35,26,58,.35) 70%,transparent 100%);
  border:none;border-radius:18px;padding:26px 8px 20px;margin-bottom:10px;
  position:relative;overflow:hidden}
.hero:before{content:"";position:absolute;inset:0;background:
  radial-gradient(500px 180px at 80% 20%,rgba(200,170,110,.10),transparent 70%);pointer-events:none}
.hero h1{font-size:2.5rem;background:linear-gradient(135deg,#c8aa6e 0%,#f5e2ac 45%,#c8aa6e 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0 0 6px}
.hero p{color:#8489b4!important;font-size:.92rem;margin:0}
.hero .badges{margin-top:12px;display:flex;gap:8px;flex-wrap:wrap}
.hero .bdg{font-size:.68rem;font-weight:700;letter-spacing:.8px;text-transform:uppercase;
  color:#c8aa6e;background:rgba(200,170,110,.08);border:1px solid rgba(200,170,110,.28);
  border-radius:999px;padding:4px 12px}

/* quiet tabs */
.stTabs [data-baseweb="tab-list"]{gap:2px;border-bottom:1px solid rgba(255,255,255,.08);
  background:transparent;padding:0}
.stTabs [data-baseweb="tab"]{background:transparent;color:#8489b4;border-radius:8px 8px 0 0;
  padding:9px 16px;font-weight:600;font-size:.85rem;transition:color .15s}
.stTabs [data-baseweb="tab"]:hover{color:#e2c78a}
.stTabs [aria-selected="true"]{background:transparent!important;color:#e2c78a!important;
  border-bottom:2px solid #c8aa6e}

/* cards */
.card{background:rgba(255,255,255,.022);border:1px solid rgba(255,255,255,.07);
  border-radius:12px;padding:18px 20px}
.top10-card{background:rgba(255,255,255,.022);border:1px solid rgba(255,255,255,.07);
  border-top:2px solid var(--tc,#c8aa6e);border-radius:12px;padding:14px 12px 12px;text-align:center;
  transition:transform .15s,border-color .15s;height:100%}
.top10-card:hover{transform:translateY(-2px);border-color:rgba(255,255,255,.18)}
.top10-card .rnk{font-size:1.55rem;font-weight:800;color:#e9e6dd;font-family:'Playfair Display',serif;line-height:1}
.top10-card .team{font-size:.85rem;font-weight:700;color:#eae7e0;margin:5px 0 2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.top10-card .idx{font-size:1rem;font-weight:700;color:#c8aa6e;font-family:'Inter',monospace}
.top10-card .delta{font-size:.72rem;font-weight:700;margin-top:3px}
.top10-card .qb{font-size:.68rem;color:#8489b4;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.top10-card .conf{display:inline-block;font-size:.6rem;font-weight:700;letter-spacing:.6px;color:#8489b4;
  border:1px solid #262c52;border-radius:999px;padding:2px 8px;margin-top:6px}

.kpi{background:rgba(255,255,255,.022);border:1px solid rgba(255,255,255,.07);border-radius:12px;
  padding:15px 16px;text-align:center;height:100%}
.kpi .lbl{font-size:.66rem;color:#8a8ea8;text-transform:uppercase;letter-spacing:1.4px;margin-bottom:5px;font-weight:700}
.kpi .val{font-size:1.75rem;font-weight:800;color:#c8aa6e;font-family:'Playfair Display',serif;line-height:1.15}
.kpi .sub{font-size:.7rem;color:#5a5e7a;margin-top:4px}

.note{background:rgba(200,170,110,.06);border:1px solid rgba(200,170,110,.16);
  border-left:3px solid #c8aa6e;border-radius:8px;padding:13px 16px;font-size:.84rem;color:#b0b4c8;margin:12px 0}
.note strong{color:#c8aa6e}

.chip{display:inline-block;font-size:.66rem;font-weight:700;letter-spacing:.5px;border-radius:999px;
  padding:2px 10px;margin-right:4px}
.chip.g{color:#7fd48b;background:rgba(110,200,122,.1);border:1px solid rgba(110,200,122,.3)}
.chip.r{color:#ef7d7d;background:rgba(224,82,82,.1);border:1px solid rgba(224,82,82,.3)}
.chip.b{color:#7ea4f2;background:rgba(74,126,237,.1);border:1px solid rgba(74,126,237,.32)}
.chip.y{color:#e2c78a;background:rgba(200,170,110,.1);border:1px solid rgba(200,170,110,.32)}

/* team banner */
.tbanner{border-radius:16px;padding:26px 32px;margin-bottom:14px;position:relative;overflow:hidden;
  background:linear-gradient(115deg,var(--c1,#1a1f42) 0%,#0d1024 62%);border:1px solid #232a52}
.tbanner .tname{font-family:'Playfair Display',serif;font-size:2.1rem;font-weight:900;color:#fff;line-height:1.05}
.tbanner .tmeta{color:rgba(255,255,255,.75);font-size:.85rem;margin-top:6px;font-weight:600}
.tbanner .bigrank{position:absolute;right:34px;top:50%;transform:translateY(-50%);
  font-family:'Playfair Display',serif;font-weight:900;font-size:3.6rem;color:rgba(255,255,255,.16)}

/* football field depth chart — muted broadcast style */
.fieldwrap{display:flex;gap:14px;flex-wrap:wrap}
.fieldcol{flex:1;min-width:330px}
.fieldttl{text-align:center;font-size:.68rem;font-weight:700;letter-spacing:2.5px;color:#6a7094;
  text-transform:uppercase;margin-bottom:6px}
.field{border-radius:10px;overflow:hidden;border:1px solid #21372a;
  background:repeating-linear-gradient(180deg,#0d1a13 0px,#0d1a13 56px,#0f1d15 56px,#0f1d15 112px)}
.endzone{background:linear-gradient(90deg,var(--c1,#333),color-mix(in srgb,var(--c1,#333) 72%,#000));
  color:rgba(255,255,255,.92);text-align:center;font-weight:700;font-size:.62rem;
  letter-spacing:5px;padding:6px 4px;text-transform:uppercase}
.frow{display:flex;justify-content:space-evenly;align-items:stretch;gap:6px;padding:10px 8px;
  border-top:1px solid rgba(255,255,255,.05)}
.pchip{background:#0a0f1e;border:1px solid #222945;border-radius:8px;
  padding:6px 9px 7px;min-width:88px;max-width:150px;text-align:center;flex:0 1 auto}
.pchip .pos{font-size:.55rem;font-weight:700;letter-spacing:1.4px;color:#6a7094}
.pchip .name{font-size:.74rem;font-weight:700;color:#e9e6dd;line-height:1.15;margin:2px 0}
.pchip .pstat{font-size:.6rem;color:#8b91b3;line-height:1.25}
.pchip .tag{font-size:.53rem;font-weight:700;margin-top:4px;letter-spacing:.8px;color:#5c6187}
.pchip.ret .tag{color:#6fa97c}
.pchip.new{border-color:#39508f}
.pchip.new .tag{color:#7ea4f2}
.pchip.aa{border-left:2px solid #c8aa6e}
.pchip.aa .name{color:#e9d9ab}
.pchip.ph{opacity:.38;border-style:dashed}

/* portal player card */
.pcard-line{display:flex;gap:10px;align-items:center;font-size:.8rem;color:#b0b4c8}
.ratingbar{height:7px;border-radius:999px;background:#1a2038;overflow:hidden;margin:6px 0}
.ratingbar>div{height:100%;border-radius:999px;background:linear-gradient(90deg,#c8aa6e,#f0d898)}

/* schedule rows */
.schrow{display:grid;grid-template-columns:44px 1fr 130px 90px 70px 46px;gap:10px;align-items:center;
  border-bottom:1px solid rgba(255,255,255,.06);padding:9px 10px;font-size:.82rem}
.schrow.home{background:rgba(200,170,110,.05);border-left:2px solid #c8aa6e}
.schrow .wk{font-weight:800;color:#8489b4;font-size:.72rem}
.schrow .opp{font-weight:700;color:#eae7e0}
.schrow .ven{color:#6a6f92;font-size:.7rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.schrow .pick-w{color:#7fd48b;font-weight:800}.schrow .pick-l{color:#ef7d7d;font-weight:800}

div[data-testid="stMetric"]{background:rgba(255,255,255,.022);border:1px solid rgba(255,255,255,.07);
  border-radius:12px;padding:14px 18px}
div[data-testid="stMetric"] label{color:#8a8ea8!important;font-size:.72rem!important;text-transform:uppercase;letter-spacing:1px}
div[data-testid="stMetric"] [data-testid="stMetricValue"]{color:#c8aa6e!important;font-family:'Playfair Display',serif!important}
div[data-testid="stExpander"]{background:rgba(255,255,255,.018);border:1px solid rgba(255,255,255,.07);border-radius:10px}
div[data-testid="stExpander"] summary{font-weight:600}
.stSelectbox label,.stMultiSelect label,.stSlider label,.stRadio label,.stCheckbox label,.stTextInput label,.stNumberInput label{
  color:#8a8ea8!important;font-size:.74rem!important;text-transform:uppercase;letter-spacing:1px;font-weight:700!important}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════
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
    ("prior_year_team_quality_score","Prior-Year Quality",20),
    ("returning_production_score","Returning Production",20),
    ("qb_score","QB Room",14),
    ("transfer_impact_score","Portal Net",13),
    ("recruiting_talent_score","Recruiting/Talent",11),
    ("coaching_continuity_score","Coaching",6),
    ("conference_strength_score","Conference",6),
    ("momentum_score","Momentum/Buzz",6),
    ("schedule_strength_score","Schedule",4),
]

# Curated NIL headliners (NIL $ isn't in any public feed — hand-verified subset)
NIL_HEADLINERS = {
    ("Darian Mensah","Miami"):"$10M", ("Drew Mestemaker","Oklahoma State"):"$7M/2yr",
    ("Sam Leavitt","LSU"):"$4M+", ("Cam Coleman","Texas"):"$3M+",
}

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

# Primary/secondary colors keyed by CFBD (v2) school names. Fallback = gold.
TEAM_COLORS = {
    "Ohio State":("#bb0000","#8d8d8d"),"Michigan":("#00274c","#ffcb05"),"Oregon":("#154733","#fee123"),
    "Penn State":("#041e42","#ffffff"),"USC":("#990000","#ffcc00"),"Washington":("#4b2e83","#b7a57a"),
    "Indiana":("#990000","#eeedeb"),"Nebraska":("#e41c38","#f5f1e7"),"Iowa":("#ffcd00","#000000"),
    "Illinois":("#e84a27","#13294b"),"Wisconsin":("#c5050c","#9b0000"),"Minnesota":("#7a0019","#ffcc33"),
    "Michigan State":("#18453b","#ffffff"),"Maryland":("#e03a3e","#ffd520"),"Rutgers":("#cc0033","#5f6a72"),
    "Northwestern":("#4e2a84","#ffffff"),"Purdue":("#cfb991","#000000"),"UCLA":("#2d68c4","#f2a900"),
    "Georgia":("#ba0c2f","#000000"),"Alabama":("#9e1b32","#828a8f"),"Texas":("#bf5700","#ffffff"),
    "Texas A&M":("#500000","#ffffff"),"LSU":("#461d7c","#fdd023"),"Ole Miss":("#ce1126","#14213d"),
    "Tennessee":("#ff8200","#58595b"),"Auburn":("#0c2340","#e87722"),"Florida":("#0021a5","#fa4616"),
    "South Carolina":("#73000a","#000000"),"Missouri":("#f1b82d","#000000"),"Arkansas":("#9d2235","#ffffff"),
    "Kentucky":("#0033a0","#ffffff"),"Mississippi State":("#660000","#ffffff"),"Vanderbilt":("#866d4b","#000000"),
    "Oklahoma":("#841617","#fdf9d8"),"Texas Tech":("#cc0000","#000000"),"Kansas State":("#512888","#d1d1d1"),
    "Kansas":("#0051ba","#e8000d"),"Oklahoma State":("#ff7300","#000000"),"TCU":("#4d1979","#a3a9ac"),
    "Baylor":("#154734","#ffb81c"),"Iowa State":("#c8102e","#f1be48"),"West Virginia":("#002855","#eaaa00"),
    "Cincinnati":("#e00122","#000000"),"UCF":("#000000","#ba9b37"),"Houston":("#c8102e","#76232f"),
    "BYU":("#002e5d","#ffffff"),"Utah":("#cc0000","#808080"),"Arizona":("#cc0033","#003366"),
    "Arizona State":("#8c1d40","#ffc627"),"Colorado":("#cfb87c","#000000"),
    "Clemson":("#f56600","#522d80"),"Florida State":("#782f40","#ceb888"),"Miami":("#f47321","#005030"),
    "North Carolina":("#7bafd4","#13294b"),"NC State":("#cc0000","#000000"),"Duke":("#003087","#ffffff"),
    "Virginia":("#232d4b","#f84c1e"),"Virginia Tech":("#630031","#cf4420"),"Louisville":("#ad0000","#000000"),
    "Pittsburgh":("#003594","#ffb81c"),"Syracuse":("#d44500","#000e54"),"Boston College":("#98002e","#bc9b6a"),
    "Wake Forest":("#9e7e38","#000000"),"Georgia Tech":("#b3a369","#003057"),"SMU":("#0033a0","#c8102e"),
    "California":("#003262","#fdb515"),"Stanford":("#8c1515","#ffffff"),
    "Notre Dame":("#0c2340","#c99700"),"UConn":("#000e2f","#e4002b"),"Army":("#000000","#d4bf91"),
    "Navy":("#00205b","#c5b783"),"Tulane":("#006747","#418fde"),"Memphis":("#003087","#898d8d"),
    "South Florida":("#006747","#cfc493"),"East Carolina":("#592a8a","#fdc82f"),"Tulsa":("#002d72","#c8102e"),
    "Boise State":("#0033a0","#d64309"),"San Diego State":("#a6192e","#000000"),"Fresno State":("#db0032","#231f20"),
    "UNLV":("#cf0a2c","#666666"),"Colorado State":("#1e4d2b","#c8c372"),"Air Force":("#003087","#8a8d8f"),
    "San José State":("#0055a2","#e5a823"),"Wyoming":("#492f24","#ffc425"),"Utah State":("#0f2439","#8a8d8f"),
    "James Madison":("#450084","#cbb677"),"App State":("#222222","#ffcc00"),"Coastal Carolina":("#006f71","#a27752"),
    "Georgia Southern":("#011e41","#87714d"),"Marshall":("#00b140","#000000"),"Old Dominion":("#003057","#7c878e"),
    "Liberty":("#002d62","#c41230"),"Western Kentucky":("#c8102e","#000000"),"Jacksonville State":("#cc0000","#000000"),
    "Toledo":("#15397f","#ffd200"),"Ohio":("#00694e","#cda077"),"Miami (OH)":("#c8102e","#000000"),
    "Bowling Green":("#fe5000","#4f2c1d"),"Northern Illinois":("#c8102e","#000000"),"Buffalo":("#005bbb","#ffffff"),
    "Texas State":("#501214","#8d734a"),"Louisiana":("#ce181e","#0a0203"),"Troy":("#8a2432","#c2c6c9"),
    "South Alabama":("#00205b","#bf0d3e"),"Arkansas State":("#cc092f","#000000"),"Georgia State":("#0039a6","#c60c30"),
    "North Texas":("#00853e","#000000"),"UTSA":("#f15a22","#002a5c"),"Rice":("#00205b","#c1c6c8"),
    "UAB":("#1e6b52","#f4c300"),"Florida Atlantic":("#003366","#cc0000"),"Charlotte":("#046a38","#b9975b"),
    "Middle Tennessee":("#0066cc","#000000"),"FIU":("#081e3f","#b6862c"),"Louisiana Tech":("#002f8b","#e31b23"),
    "Southern Miss":("#ffab00","#000000"),"New Mexico State":("#8c0b42","#ffffff"),"Sam Houston":("#f56423","#0d3468"),
    "Kennesaw State":("#ffc629","#000000"),"Delaware":("#00539f","#ffd200"),"Missouri State":("#5e0009","#889296"),
    "UL Monroe":("#800029","#ffb300"),"Hawai'i":("#024731","#c8c8c8"),"Nevada":("#003366","#807f84"),
    "New Mexico":("#ba0c2f","#63666a"),"UTEP":("#ff8200","#041e42"),"Akron":("#041e42","#a89968"),
    "Ball State":("#ba0c2f","#000000"),"Central Michigan":("#6a0032","#ffc82e"),"Eastern Michigan":("#006633","#ffffff"),
    "Kent State":("#002664","#eaab00"),"Western Michigan":("#6c4023","#b5a167"),"UMass":("#881c1c","#000000"),
    "Washington State":("#981e32","#5e6a71"),"Oregon State":("#dc4405","#000000"),
}
CONF_COLORS = {
    "SEC":"#ffd046","Big Ten":"#6ea8ff","Big 12":"#ff6e6e","ACC":"#7fd48b","Pac-12":"#4ecdc4",
    "American Athletic":"#c792ea","Mountain West":"#f78c6c","Sun Belt":"#f4e04d",
    "Conference USA":"#89ddff","Mid-American":"#b2ccd6","FBS Independents":"#e2c78a",
}
def team_color(t): return TEAM_COLORS.get(t,("#c8aa6e","#3a3e5a"))[0]
def team_color2(t): return TEAM_COLORS.get(t,("#c8aa6e","#3a3e5a"))[1]
def txt_color(t):
    """Team color lightened until it reads on the dark background."""
    h=team_color(t).lstrip("#")
    r,g,b=(int(h[i:i+2],16) for i in (0,2,4))
    while (0.299*r+0.587*g+0.114*b)/255 < 0.52:
        r=int(r+(255-r)*.30); g=int(g+(255-g)*.30); b=int(b+(255-b)*.30)
    return f"#{r:02x}{g:02x}{b:02x}"

GOLD="#c8aa6e"; BLUE="#4a7eed"; RED="#e05252"; GREEN="#6ec87a"; GRAY="#3a3e5a"; PURPLE="#a87ee6"
PL=dict(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(10,13,26,.55)",
        font=dict(family="Inter,sans-serif",color="#b0b4c8"),
        title_font=dict(family="Playfair Display,serif",color="#eae7e0",size=17),
        hoverlabel=dict(bgcolor="#161830",bordercolor="#c8aa6e",font_color="#e8e0d0"))
AX=dict(gridcolor="#161a2e",zerolinecolor="#1e2240")
def sf(f): f.update_xaxes(**AX); f.update_yaxes(**AX); return f
def gc(row,col,d=50):
    try: return float(row[col]) if col in row.index and pd.notna(row[col]) else d
    except: return d
def esc(s): return html.escape(str(s))
def md_b(s):
    """Convert **bold** markdown to <b> for strings rendered inside raw HTML."""
    return re.sub(r"\*\*(.+?)\*\*",r"<b>\1</b>",s)

# ═══════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_data
def load_v2():
    for p in ["cfb_power_index_v2.csv","data/processed/cfb_power_index_v2.csv"]:
        if os.path.exists(p): return pd.read_csv(p)
    return pd.DataFrame()

@st.cache_data
def load_v1():
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

@st.cache_data
def load_player_stats():
    for p in ["data/raw/2025_player_stats.csv","2025_player_stats.csv"]:
        if os.path.exists(p): return pd.read_csv(p)
    return pd.DataFrame()

@st.cache_data
def load_portal():
    for p in ["data/raw/2026_transfer_portal_cfbd.csv","2026_transfer_portal_cfbd.csv"]:
        if not os.path.exists(p): continue
        df = pd.read_csv(p)
        df["player"]=(df["firstName"].fillna("").astype(str).str.strip()+" "
                      +df["lastName"].fillna("").astype(str).str.strip()).str.strip()
        df["rating"]=pd.to_numeric(df.get("rating"),errors="coerce")
        df["stars"]=pd.to_numeric(df.get("stars"),errors="coerce")
        df["position"]=df.get("position","").astype(str).str.upper().str.strip()
        return df
    return pd.DataFrame()

@st.cache_data
def load_departures():
    """Curated NFL-draft declarations + graduating seniors after 2025 —
    players the 2025 stat feed can't know are gone. Hand-editable CSV."""
    for p in ["data/raw/2026_departures.csv"]:
        if os.path.exists(p):
            d=pd.read_csv(p)
            d["_nm"]=d["player"].astype(str).str.lower().str.strip()
            # Alias rows (e.g. "CJ" vs "C.J.") exist to catch feed spelling; collapse
            # them for display via a punctuation-free key.
            d["_key"]=d["_nm"].str.replace(r"[.\s]","",regex=True)+"|"+d["team"].astype(str)
            return d
    return pd.DataFrame()

@st.cache_data
def load_records():
    for p in ["data/raw/2025_records.csv"]:
        if not os.path.exists(p): continue
        r=pd.read_csv(p)
        r=r[r.get("classification","fbs").astype(str)=="fbs"]
        return r
    return pd.DataFrame()

@st.cache_data
def load_adv():
    for p in ["data/raw/2025_team_advanced_season_stats.csv"]:
        if os.path.exists(p): return pd.read_csv(p)
    return pd.DataFrame()

@st.cache_data
def load_qbs():
    for p in ["data/raw/2026_qb_starters.csv"]:
        if not os.path.exists(p): continue
        q=pd.read_csv(p)
        for c in ["att_2025","yds_2025","td_2025","int_2025","pct_2025","ypa_2025"]:
            if c in q.columns: q[c]=pd.to_numeric(q[c],errors="coerce")
        return q
    return pd.DataFrame()

@st.cache_data
def pstats_wide():
    """Per-player wide 2025 stat table: passing_YDS, rushing_YDS, defensive_SACKS…"""
    ps=load_player_stats()
    if ps.empty or not {"category","statType","stat","player","team"}.issubset(ps.columns):
        return pd.DataFrame()
    ps=ps[ps["category"].isin(["passing","rushing","receiving","defensive","interceptions"])].copy()
    ps["stat"]=pd.to_numeric(ps["stat"],errors="coerce")
    ps["key"]=ps["category"].astype(str).str.lower()+"_"+ps["statType"].astype(str)
    wide=ps.pivot_table(index=["playerId","player","position","team"],
                        columns="key",values="stat",aggfunc="first").reset_index()
    wide.columns.name=None
    wide["_nm"]=wide["player"].astype(str).str.lower().str.strip()
    return wide

v2=load_v2(); v1=load_v1(); sched_df=load_sched()
portal_df=load_portal(); records_df=load_records(); adv_df=load_adv(); qbs_df=load_qbs()

# Normalize V2 column names + join 2025 rank movement from V1
if not v2.empty and "School" not in v2.columns:
    for alt in ["team","Team","school"]:
        if alt in v2.columns: v2=v2.rename(columns={alt:"School"}); break
if not v2.empty:
    if "rank_v2" not in v2.columns:
        for alt in ["Rank_2026","power_rank_v2"]:
            if alt in v2.columns: v2=v2.rename(columns={alt:"rank_v2"}); break
    if not v1.empty:
        v1rank={to_v2_name(s):r for s,r in zip(v1["School"],v1["Power_Rank"])}
        v2["Rank_2025"]=v2["School"].map(v1rank)
    if "Rank_2025" not in v2.columns: v2["Rank_2025"]=v2["rank_v2"]
    v2["Rank_2025"]=pd.to_numeric(v2["Rank_2025"],errors="coerce").fillna(v2["rank_v2"])
    v2["delta_vs_2025"]=(v2["Rank_2025"]-v2["rank_v2"]).astype(int)
    if "projected_qb" in v2.columns: v2["qb_name"]=v2["projected_qb"].fillna("TBD")
    else: v2["qb_name"]="TBD"
    st_l=v2.get("qb_status",pd.Series("",index=v2.index)).astype(str).str.lower()
    v2["qb_type"]=np.select(
        [st_l.str.contains("returning"),st_l.str.contains("transfer")],
        ["returning","transfer"],default="battle")

has_v1 = not v1.empty
has_v2 = not v2.empty
if has_v2: teams_sorted=v2.sort_values("rank_v2")["School"].tolist()
elif has_v1: teams_sorted=v1.sort_values("Power_Rank")["School"].tolist()
else: teams_sorted=[]

REC_2025={}
if not records_df.empty and {"team","total.wins","total.losses"}.issubset(records_df.columns):
    REC_2025={t:f"{int(w)}–{int(l)}" for t,w,l in zip(records_df["team"],
              records_df["total.wins"],records_df["total.losses"])}

STRENGTH_COL="team_strength_rating" if has_v2 and "team_strength_rating" in v2.columns else "power_index_v2"

def _sched_keys():
    hc="home_team" if "home_team" in sched_df.columns else "homeTeam"
    ac="away_team" if "away_team" in sched_df.columns else "awayTeam"
    ncol=next((c for c in ["neutral_site","neutralSite","neutral"] if c in sched_df.columns),None)
    wcol=next((c for c in ["week","Week"] if c in sched_df.columns),None)
    return hc,ac,ncol,wcol

def team_games(team):
    """2026 games with opponent rank, venue, win prob (strength-based + HFA)."""
    if sched_df.empty or not has_v2: return pd.DataFrame()
    hc,ac,ncol,wcol=_sched_keys()
    if hc not in sched_df.columns: return pd.DataFrame()
    pi=dict(zip(v2["School"],v2[STRENGTH_COL]))
    rk=dict(zip(v2["School"],v2["rank_v2"]))
    g=sched_df[(sched_df[hc]==team)|(sched_df[ac]==team)].copy()
    rows=[]
    for _,r in g.iterrows():
        opp=r[ac] if r[hc]==team else r[hc]
        neutral=bool(r[ncol]) if ncol and pd.notna(r.get(ncol)) else False
        site="Neutral" if neutral else ("Home" if r[hc]==team else "Away")
        if opp in pi:
            hfa=0 if neutral else (3.0 if site=="Home" else -3.0)
            p=1/(1+np.exp(-0.1*((pi[team]-pi[opp])+hfa)))
        else:
            p=0.90
        rows.append({"Wk":r.get(wcol,np.nan) if wcol else np.nan,"Opponent":opp,"Site":site,
                     "Venue":r.get("venue",""),"Opp Rank":rk.get(opp,np.nan),
                     "Win %":round(p*100),"Pick":"W" if p>=0.5 else "L"})
    out=pd.DataFrame(rows)
    return out.sort_values("Wk") if "Wk" in out.columns and out["Wk"].notna().any() else out

@st.cache_data
def projected_records():
    if sched_df.empty or not has_v2: return pd.DataFrame()
    hc,ac,ncol,_=_sched_keys()
    if hc not in sched_df.columns: return pd.DataFrame()
    pi=dict(zip(v2["School"],v2[STRENGTH_COL]))
    rows=[]
    for team in v2["School"]:
        g=sched_df[(sched_df[hc]==team)|(sched_df[ac]==team)]
        w=l=0
        for _,r in g.iterrows():
            opp=r[ac] if r[hc]==team else r[hc]
            if opp in pi:
                neutral=bool(r[ncol]) if ncol and pd.notna(r.get(ncol)) else False
                hfa=0 if neutral else (3.0 if r[hc]==team else -3.0)
                p=1/(1+np.exp(-0.1*((pi[team]-pi[opp])+hfa)))
                w+=1 if p>=0.5 else 0; l+=0 if p>=0.5 else 1
            else: w+=1
        rows.append({"School":team,"Proj W":w,"Proj L":l,"Games":w+l})
    return pd.DataFrame(rows)

# ═══════════════════════════════════════════════════════════════════════════════
# ROSTER / DEPTH CHART HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_data
def all_america_keys(fbs_teams:tuple):
    """Model All-Americans: top-5 nationally at each position by 2025 production.
    Keyed by (player_lower, 2025 team) so portal players keep their star."""
    w=pstats_wide()
    if w.empty: return set()
    w=w[w["team"].isin(fbs_teams)].fillna(0)
    picks=set()
    def top(mask,col,n=5):
        if col not in w.columns: return
        for _,r in w[mask].nlargest(n,col).iterrows():
            picks.add((str(r["player"]).lower(),r["team"]))
    top(w["position"]=="QB","passing_YDS")
    top(w["position"]=="RB","rushing_YDS")
    top(w["position"]=="WR","receiving_YDS")
    top(w["position"]=="TE","receiving_YDS",3)
    top(w["position"].isin(["DL","DE","DT","NT","EDGE"]),"defensive_SACKS")
    top(w["position"]=="LB","defensive_TOT")
    top(w["position"].isin(["CB","S","DB"]),"interceptions_INT")
    return picks

def stat_line(r):
    """Compact human stat line from a wide player row."""
    def g(c):
        v=r.get(c,0)
        return 0 if pd.isna(v) else float(v)
    bits=[]
    if g("passing_YDS")>200: bits.append(f"{int(g('passing_YDS')):,} yds · {int(g('passing_TD'))} TD · {int(g('passing_INT'))} INT")
    if g("rushing_YDS")>150: bits.append(f"{int(g('rushing_YDS')):,} rush · {int(g('rushing_TD'))} TD")
    if g("receiving_YDS")>100: bits.append(f"{int(g('receiving_YDS')):,} rec · {int(g('receiving_TD'))} TD")
    if g("defensive_SACKS")>=2: bits.append(f"{g('defensive_SACKS'):g} sacks · {g('defensive_TFL'):g} TFL")
    elif g("defensive_TOT")>=20: bits.append(f"{int(g('defensive_TOT'))} tkl")
    if g("interceptions_INT")>=1: bits.append(f"{int(g('interceptions_INT'))} INT")
    return " · ".join(bits[:2]) if bits else "—"

@st.cache_data
def team_pool(team):
    """All candidate 2026 players for a team: 2025 roster minus portal exits and
    known draft/graduation departures, plus portal arrivals (with their 2025
    stats from their old school)."""
    w=pstats_wide()
    if w.empty: return pd.DataFrame(),pd.DataFrame(),pd.DataFrame(),pd.DataFrame()
    tw=w[w["team"]==team].copy()
    outs=portal_df[portal_df["origin"]==team].copy() if not portal_df.empty else pd.DataFrame()
    ins=portal_df[portal_df["destination"]==team].copy() if not portal_df.empty else pd.DataFrame()
    deps=load_departures()
    tdep=deps[deps["team"]==team].copy() if not deps.empty else pd.DataFrame()
    out_names=set(outs["player"].str.lower()) if not outs.empty else set()
    dep_names=set(tdep["_nm"]) if not tdep.empty else set()  # all alias spellings
    tw["status"]=np.where(tw["_nm"].isin(out_names|dep_names),"departed","returning")

    # ── Reconcile against the live 2026 roster ──────────────────────────────────
    # Portal/departure feeds are from the off-season and go stale: players withdraw
    # or the landing spot is never recorded. The live roster is the source of truth
    # for who is actually on the team right now, so:
    #   • anyone on the live roster is RETURNING (kills false departures)
    #   • a 2025 contributor NOT on the live roster is genuinely DEPARTED
    #   • portal ARRIVALS count only if they actually landed (on the roster)
    #   • portal/curated DEPARTURES count only if they're truly gone
    keys = live_roster_keys(team)
    if keys:
        tw["status"]=np.where(tw["player"].map(lambda n: on_live_roster(n,keys)),
                              "returning","departed")
        if not outs.empty:
            outs=outs[~outs["player"].map(lambda n: on_live_roster(n,keys))]
        if not ins.empty:
            ins=ins[ins["player"].map(lambda n: on_live_roster(n,keys))]
        if not tdep.empty:
            tdep=tdep[~tdep["player"].map(lambda n: on_live_roster(n,keys))]
    if not tdep.empty: tdep=tdep.drop_duplicates(subset="_key")  # collapse aliases for display
    tw["origin"]="";tw["rating"]=np.nan;tw["stars"]=np.nan
    rows=[]
    if not ins.empty:
        for _,r in ins.iterrows():
            hist=w[(w["_nm"]==str(r["player"]).lower())&(w["team"]==r["origin"])]
            base=hist.iloc[0].to_dict() if len(hist) else {}
            base.update({"player":r["player"],"position":r["position"],"team":team,
                         "status":"portal","origin":r["origin"],"rating":r["rating"],
                         "stars":r["stars"],"_nm":str(r["player"]).lower()})
            rows.append(base)
    pool=pd.concat([tw,pd.DataFrame(rows)],ignore_index=True) if rows else tw

    # Fold in live-roster players with no 2025 stats (true freshmen, unlisted
    # transfers, walk-ons now on the two-deep) so the chart is exhaustive & current.
    if keys:
        ros=live_roster_df(team)
        if ros is not None and not ros.empty:
            pk=set(norm_name(n) for n in pool["player"])
            pini=set((k.split()[-1],k.split()[0][0]) for k in pk if len(k.split())>=2)
            def _in_pool(nm):
                k=norm_name(nm)
                if not k or k in pk: return True
                p=k.split(); return len(p)>=2 and (p[-1],p[0][0]) in pini
            extra=[{"player":r["name"],"position":slot_pos(r["pos"]),"team":team,
                    "status":"returning","origin":"","rating":np.nan,"stars":np.nan,
                    "_nm":str(r["name"]).lower()}
                   for _,r in ros.iterrows() if not _in_pool(r["name"])]
            if extra:
                pool=pd.concat([pool,pd.DataFrame(extra)],ignore_index=True)

    num_cols=[c for c in pool.columns if c.startswith(("passing_","rushing_","receiving_","defensive_","interceptions_"))]
    for c in num_cols: pool[c]=pd.to_numeric(pool[c],errors="coerce").fillna(0)
    return pool,ins,outs,tdep

SLOT_DEFS=[  # (unit, slot label, position filter, sort metric builder, count)
    ("OFF","WR",{"WR"},lambda d:d.get("receiving_YDS",0),3),
    ("OFF","TE",{"TE"},lambda d:d.get("receiving_YDS",0),1),
    ("OFF","RB",{"RB","FB"},lambda d:d.get("rushing_YDS",0),2),
    ("DEF","DL",{"DL","DE","DT","NT","EDGE"},lambda d:d.get("defensive_SACKS",0)*3+d.get("defensive_TFL",0)+d.get("defensive_TOT",0)*.1,4),
    ("DEF","LB",{"LB"},lambda d:d.get("defensive_TOT",0)+d.get("defensive_SACKS",0)*2,3),
    ("DEF","CB",{"CB"},lambda d:d.get("defensive_PD",0)*2+d.get("interceptions_INT",0)*3+d.get("defensive_TOT",0)*.2,2),
    ("DEF","S",{"S","DB"},lambda d:d.get("defensive_TOT",0)*.4+d.get("interceptions_INT",0)*3+d.get("defensive_PD",0),2),
]

def pick_depth(team):
    pool,ins,outs,tdep=team_pool(team)
    picks={}
    if pool.empty: return picks,ins,outs,tdep
    avail=pool[pool["status"]!="departed"].copy()
    used=set()
    for unit,slot,posset,metric,n in SLOT_DEFS:
        sub=avail[avail["position"].isin(posset)].copy()
        if sub.empty: picks[slot]=[]; continue
        sub["_m"]=sub.apply(lambda r:metric(r)+(50 if r["status"]=="portal" and pd.notna(r.get("rating")) and r.get("rating",0)>=0.92 else 0),axis=1)
        sub=sub[~sub["_nm"].isin(used)].sort_values("_m",ascending=False).head(n)
        used|=set(sub["_nm"])
        picks[slot]=sub.to_dict("records")
    return picks,ins,outs,tdep

def chip_html(p,aa,slot):
    nm=str(p.get("player","?"))
    cls=["pchip"]
    if p.get("status")=="portal":
        cls.append("new"); tag=f"PORTAL · {esc(str(p.get('origin','')).upper())}"
    elif p.get("status")=="qb_ret": cls.append("ret"); tag="RETURNING STARTER"
    elif p.get("status")=="qb_new": cls.append("new"); tag=f"TRANSFER · {esc(str(p.get('origin','')).upper())}" if p.get("origin") else "TRANSFER"
    elif p.get("status")=="qb_battle": tag="UNSETTLED"
    else: cls.append("ret"); tag="RETURNING"
    key=(nm.lower(),p.get("origin") if p.get("status")=="portal" else p.get("team"))
    if aa and key in aa:
        cls.append("aa"); tag+=" · ALL-AMERICAN ★"
    sl=p.get("_statline") or stat_line(p)
    return (f'<div class="{" ".join(cls)}"><div class="pos">{esc(slot)}</div>'
            f'<div class="name">{esc(nm)}</div><div class="pstat">{esc(sl)}</div>'
            f'<div class="tag">{tag}</div></div>')

def ph_chip(label,note="no data"):
    return (f'<div class="pchip ph"><div class="pos">{esc(label)}</div>'
            f'<div class="name">—</div><div class="pstat">{esc(note)}</div><div class="tag"></div></div>')

def field_html(team,picks,aa):
    c1=team_color(team)
    qbrow=qbs_df[qbs_df["team"]==team] if not qbs_df.empty else pd.DataFrame()
    qb_chip=""
    if not qbrow.empty:
        q=qbrow.iloc[0]
        status=str(q.get("status","")).lower()
        qstat="qb_ret" if "returning" in status else ("qb_new" if "transfer" in status else "qb_battle")
        line="—"
        if pd.notna(q.get("yds_2025")) and q.get("yds_2025",0)>0:
            line=f"{int(q['yds_2025']):,} yds · {int(q.get('td_2025',0))} TD · {int(q.get('int_2025',0))} INT"
        qb_chip=chip_html({"player":q["qb"],"status":qstat,"team":team,
                           "origin":q.get("prev_team_2025",""),"_statline":line},aa,"QB")
    else:
        qb_chip=""
    def row(items,slot,minn=0):
        if not items: return ""
        chips="".join(chip_html(p,aa,slot) for p in items)
        return f'<div class="frow">{chips}</div>'
    wr=picks.get("WR",[]); te=picks.get("TE",[]); rb=picks.get("RB",[])
    dl=picks.get("DL",[]); lb=picks.get("LB",[]); cb=picks.get("CB",[]); s=picks.get("S",[])
    off=(f'<div class="fieldcol"><div class="fieldttl">Offense — projected 2026</div>'
         f'<div class="field" style="--c1:{c1}"><div class="endzone">{esc(team)}</div>'
         f'{row(wr[:2]+te[:1],"WR/TE")}'
         f'<div class="frow">{qb_chip}{"".join(chip_html(p,aa,"WR") for p in wr[2:3])}</div>'
         f'{row(rb,"RB")}'
         f'</div></div>')
    dfd=(f'<div class="fieldcol"><div class="fieldttl">Defense — projected 2026</div>'
         f'<div class="field" style="--c1:{c1}"><div class="endzone">DEFENSE</div>'
         f'{row(dl,"DL")}{row(lb,"LB")}'
         f'{row(cb[:1]+s+cb[1:2],"DB")}'
         f'</div></div>')
    return f'<div class="fieldwrap">{off}{dfd}</div>'

# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="hero">
  <h1>CFB Power Index</h1>
  <p>Live 2026 season tracking + my preseason projection model — AP poll, scoreboard, FPI, per-team schedules, strength of schedule, rosters &amp; a rest-of-season predictor · Andrew White</p>
  <div class="badges">
    <span class="bdg">🔴 Live from ESPN</span>
    <span class="bdg">{len(v2) if has_v2 else 0} FBS teams</span>
    <span class="bdg">{len(portal_df):,} portal moves tracked</span>
    <span class="bdg">9-component model + FPI blend</span>
    <span class="bdg">2025 CFP: 9/11 bracket · champ ✓</span>
  </div>
</div>""", unsafe_allow_html=True)

if not has_v1 and not has_v2:
    st.error("No data found. Run `python model_v2.py` to generate `cfb_power_index_v2.csv` and ensure `cfb_combined_data.xlsx` is present.")
    st.stop()

# ── Top navigation (session-state router so clicks elsewhere can switch pages) ──
PAGE_LIVE="🔴 Live 2026"; PAGE_TEAM="📅 Team 2026"; PAGE_CFP="🏆 Playoff Predictor"
PAGES=[PAGE_LIVE,PAGE_TEAM,PAGE_CFP,"Preseason Rankings","Team HQ","Game Predictor",
       "Portal Lab","Player Stats","2025 CFP Retro","Methodology"]
if "page" not in st.session_state: st.session_state["page"]=PAGE_LIVE

# FBS team directory (cached) — used for click-through validation + team picker
FBS_TEAMS=L.get_fbs_teams()
FBS_LIST=FBS_TEAMS["team"].tolist() if not FBS_TEAMS.empty else []
FBS_SET=set(FBS_LIST)
# Click-through target — set either by a ?team= link (any logo/name is a link) or
# by a button; both funnel here and route to the Team 2026 page.
from urllib.parse import quote
_qp_team = st.query_params.get("team")
if _qp_team:
    if _qp_team in FBS_SET:
        st.session_state["live_team"]=_qp_team
        st.session_state["page"]=PAGE_TEAM
    try: del st.query_params["team"]
    except Exception: pass
_goto=st.session_state.pop("_goto_team",None)
if _goto and _goto in FBS_SET:
    st.session_state["live_team"]=_goto
    st.session_state["page"]=PAGE_TEAM

st.markdown('<div class="navmark"></div>', unsafe_allow_html=True)
page=st.radio("Navigation",PAGES,key="page",horizontal=True,label_visibility="collapsed")

def team_link(team_name, inner_html):
    """Wrap arbitrary HTML in a link that opens the team's page (no-op if non-FBS)."""
    if team_name not in FBS_SET:
        return inner_html
    return (f'<a href="?team={quote(str(team_name))}" target="_self" '
            f'class="tlink">{inner_html}</a>')

def team_button(team_name,key,label=None):
    """A small button that jumps to a team's Team 2026 page (if it's FBS)."""
    if team_name not in FBS_SET: return
    if st.button(label or f"→ {team_name}",key=key,use_container_width=True):
        st.session_state["_goto_team"]=team_name
        st.rerun()

AA_KEYS=all_america_keys(tuple(v2["School"])) if has_v2 else set()

# ══════════════════════════════════════════════════════════════════════════════
# LIVE DATA HELPERS  (ESPN name -> my v2 "School" name, for preseason cross-link)
# ══════════════════════════════════════════════════════════════════════════════
ESPN_TO_V2 = {
    "Appalachian State":"App State","Southern Mississippi":"Southern Miss",
    "Louisiana Monroe":"UL Monroe","UL Monroe":"UL Monroe","Hawai'i":"Hawai'i",
    "Connecticut":"UConn","San José State":"San José State","San Jose State":"San José State",
    "Massachusetts":"UMass","Sam Houston State":"Sam Houston","Miami":"Miami",
}
def espn_to_school(name):
    if name is None: return None
    if name in ESPN_TO_V2: return ESPN_TO_V2[name]
    if has_v2 and name in set(v2["School"]): return name
    return name
def preseason_rank(espn_name):
    """Best-effort lookup of my preseason Power Index rank for an ESPN team name."""
    if not has_v2: return None
    s = espn_to_school(espn_name)
    m = v2[v2["School"] == s]
    return int(m.iloc[0]["rank_v2"]) if not m.empty else None

# ── Live-roster reconciliation (fixes stale portal departures/arrivals) ─────────
V2_TO_ESPN = {v: k for k, v in ESPN_TO_V2.items()}
def school_to_espn(s): return V2_TO_ESPN.get(s, s)

def norm_name(n):
    """Normalize a player name for matching across ESPN / CFBD feeds."""
    n = str(n).lower()
    n = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b\.?", "", n)
    n = re.sub(r"[^a-z ]", " ", n)
    return re.sub(r"\s+", " ", n).strip()

@st.cache_data(ttl=1800, show_spinner=False)
def live_roster_df(school):
    """The live 2026 ESPN roster for a School name, or empty if unavailable."""
    if FBS_TEAMS.empty: return pd.DataFrame()
    row = FBS_TEAMS[FBS_TEAMS["team"] == school_to_espn(school)]
    if row.empty: return pd.DataFrame()
    ros = L.get_team_roster(row.iloc[0]["team_id"])
    return ros if ros is not None else pd.DataFrame()

def live_roster_keys(school):
    """(full-name set, {(last, first-initial)}) for a team's live 2026 roster, or
    None when unavailable — callers then skip reconciliation (never fabricate a
    departure from missing data)."""
    ros = live_roster_df(school)
    if ros is None or ros.empty: return None
    full, ini = set(), set()
    for nm in ros["name"]:
        k = norm_name(nm)
        if not k: continue
        full.add(k)
        p = k.split()
        if len(p) >= 2: ini.add((p[-1], p[0][0]))
    return full, ini

# ESPN roster position code -> the position bucket the depth-chart slots use.
ESPN_POS_TO_SLOT = {
    "FB":"RB","OLB":"LB","ILB":"LB","MLB":"LB","DE":"DL","DT":"DL","NT":"DL",
    "EDGE":"DL","SS":"S","FS":"S","DB":"S",
}
def slot_pos(pos): return ESPN_POS_TO_SLOT.get(str(pos).upper(), str(pos).upper())

def on_live_roster(name, keys):
    """True if `name` plausibly matches someone on the live roster. Unknown keys
    (None) return True so we never invent a departure when the feed is down."""
    if not keys: return True
    full, ini = keys
    k = norm_name(name)
    if not k: return True
    if k in full: return True
    p = k.split()
    return len(p) >= 2 and (p[-1], p[0][0]) in ini

def trend_chip(trend):
    t = str(trend)
    if t in ("-", "", "nan", "None"): return '<span style="color:#5a5e7a">—</span>'
    if t.startswith("+"): return f'<span style="color:#7fd48b;font-weight:700">▲ {t[1:]}</span>'
    if t.startswith("-"): return f'<span style="color:#ef7d7d;font-weight:700">▼ {t[1:]}</span>'
    return f'<span style="color:#8489b4">{esc(t)}</span>'

# ── Unified power ratings: blend live FPI with my preseason model (points scale) ─
def power_ratings():
    """One table per FBS team: team_id, name, conf, logo, record, fpi, my rating,
    blended rating (65% FPI / 35% mine) + ESPN's FPI odds columns. Everything the
    playoff model needs, all keyed by ESPN team_id."""
    fpi = L.get_fpi(); standings = L.get_standings()
    if fpi.empty:
        return pd.DataFrame()
    df = fpi.copy()
    df["team_id"] = df["team_id"].astype(str)
    fv = pd.to_numeric(df.get("fpi"), errors="coerce")
    fpi_std = float(fv.std()) or 12.0
    df["fpi_pts"] = fv
    id2loc = dict(zip(FBS_TEAMS["team_id"].astype(str), FBS_TEAMS["team"])) if not FBS_TEAMS.empty else {}
    id2conf = dict(zip(standings["team_id"].astype(str), standings["conf"])) if not standings.empty else {}
    id2rec = dict(zip(standings["team_id"].astype(str), standings["overall"])) if not standings.empty else {}
    tsr = {}
    if has_v2 and "team_strength_rating" in v2.columns:
        m = float(v2["team_strength_rating"].mean()); s = float(v2["team_strength_rating"].std()) or 1.0
        sch = dict(zip(v2["School"], v2["team_strength_rating"]))
        for tid, loc in id2loc.items():
            s2 = espn_to_school(loc)
            if s2 in sch:
                tsr[tid] = (sch[s2] - m) / s * fpi_std
    def _blend(r):
        f = r["fpi_pts"]; my = tsr.get(r["team_id"])
        if pd.notna(f) and my is not None: return 0.65 * f + 0.35 * my
        return f if pd.notna(f) else (my if my is not None else -15.0)
    df["blended"] = df.apply(_blend, axis=1)
    df["name"] = df["team_id"].map(id2loc).fillna(df["team"])
    df["conf"] = df["team_id"].map(id2conf)
    df["record"] = df["team_id"].map(id2rec)
    return df.sort_values("blended", ascending=False).reset_index(drop=True)

def project_cfp_field(pr):
    """12-team field: 5 highest-rated conference champions get auto bids, then the
    7 best remaining at-large teams; all 12 straight-seeded by blended rating.
    Independents can't win a conference. Returns a seeded DataFrame (seed 1..12)."""
    if pr is None or pr.empty:
        return pd.DataFrame()
    NON_CONF = {"FBS Indep.", "FBS Independents", "Independent", None}
    champs = []
    for conf, grp in pr[~pr["conf"].isin(NON_CONF)].dropna(subset=["conf"]).groupby("conf"):
        top = grp.sort_values("blended", ascending=False).iloc[0]
        champs.append(top)
    champs = pd.DataFrame(champs).sort_values("blended", ascending=False)
    auto = champs.head(5)
    auto_ids = set(auto["team_id"])
    at_large = pr[~pr["team_id"].isin(auto_ids)].head(7)
    field = pd.concat([auto, at_large]).sort_values("blended", ascending=False).reset_index(drop=True)
    field = field.head(12).copy()
    field["seed"] = range(1, len(field) + 1)
    field["auto"] = field["team_id"].isin(auto_ids)
    return field

def simulate_bracket(field, n=4000):
    """Monte-Carlo the 12-team bracket (top 4 seeds bye; higher seed hosts round 1;
    QF+ neutral) off blended ratings. Returns per-seed F4/final/title odds."""
    import numpy as _np, math as _math
    if field is None or len(field) < 12:
        return field
    r = field["blended"].to_numpy()
    def wp(a, b, hfa=0.0):
        return 0.5 * (1 + _math.erf((r[a] - r[b] + hfa) / (16.5 * _math.sqrt(2))))
    rng = _np.random.default_rng(7)
    f4 = _np.zeros(12); fin = _np.zeros(12); champ = _np.zeros(12)
    pairs = [(4, 11), (5, 10), (6, 9), (7, 8)]   # seeds 5v12,6v11,7v10,8v9 (0-indexed)
    for _ in range(n):
        w = {}
        for hi, lo in pairs:
            w[(hi, lo)] = hi if rng.random() < wp(hi, lo, 2.4) else lo
        # quarterfinals (reseed-free standard bracket), neutral sites
        qf = [(0, w[(7, 8)]), (3, w[(4, 11)]), (2, w[(5, 10)]), (1, w[(6, 9)])]
        qw = [a if rng.random() < wp(a, b) else b for a, b in qf]
        for x in qw: f4[x] += 1
        sf = [(qw[0], qw[1]), (qw[3], qw[2])]
        sw = [a if rng.random() < wp(a, b) else b for a, b in sf]
        for x in sw: fin[x] += 1
        a, b = sw
        champ[a if rng.random() < wp(a, b) else b] += 1
    out = field.copy()
    out["p_f4"] = (f4 / n * 100).round(1)
    out["p_final"] = (fin / n * 100).round(1)
    out["p_title"] = (champ / n * 100).round(1)
    return out

# ══════════════════════════════════════════════════════════════════════════════
# LIVE-TAB STYLING
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
.aprow{display:grid;grid-template-columns:34px 34px 1fr 62px 54px 66px;gap:10px;align-items:center;
  padding:8px 12px;border-bottom:1px solid rgba(255,255,255,.05);font-size:.84rem}
.aprow:hover{background:rgba(255,255,255,.03)}
.aprow .r{font-family:'Playfair Display',serif;font-weight:800;font-size:1.15rem;color:#e9e6dd;text-align:center}
.aprow img{width:28px;height:28px;object-fit:contain}
.aprow .tm{font-weight:700;color:#eae7e0}.aprow .rec{color:#8489b4;font-size:.78rem}
.mcard{background:rgba(255,255,255,.025);border:1px solid rgba(255,255,255,.08);border-radius:14px;
  padding:14px 16px;height:100%;transition:transform .15s,border-color .15s}
.mcard:hover{transform:translateY(-2px);border-color:rgba(200,170,110,.35)}
.mcard .mt{display:flex;align-items:center;gap:9px;margin:4px 0}
.mcard .mt img{width:26px;height:26px;object-fit:contain}
.mcard .mt .nm{font-weight:700;color:#eae7e0;font-size:.92rem}
.mcard .mt .rk{font-size:.66rem;font-weight:800;color:#0a0d18;background:#c8aa6e;border-radius:5px;padding:1px 5px}
.mcard .vs{color:#5a5e7a;font-size:.66rem;font-weight:700;letter-spacing:2px;margin:2px 0}
.mcard .meta{margin-top:9px;padding-top:9px;border-top:1px solid rgba(255,255,255,.06);
  display:flex;justify-content:space-between;font-size:.7rem;color:#8489b4}
.mcard .meta b{color:#c8aa6e}
.livehdr{display:flex;align-items:center;gap:10px;margin:4px 0 2px}
.livedot{width:9px;height:9px;border-radius:50%;background:#e05252;box-shadow:0 0 0 0 rgba(224,82,82,.6);
  animation:pulse 1.8s infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(224,82,82,.55)}70%{box-shadow:0 0 0 9px rgba(224,82,82,0)}100%{box-shadow:0 0 0 0 rgba(224,82,82,0)}}
.gsc{font-family:'Playfair Display',serif;font-weight:800;font-size:1.05rem;color:#eae7e0}
.gsc.win{color:#7fd48b}.gsc.loss{color:#ef7d7d}

/* clickable AP-poll rows (dark, on-theme) */
.aprow2{display:grid;grid-template-columns:40px 32px 1fr 60px 44px;gap:12px;align-items:center;
  padding:9px 14px;border-bottom:1px solid rgba(255,255,255,.05)}
.aprow2:hover{background:rgba(200,170,110,.06)}
.aprow2 .r{font-family:'Playfair Display',serif;font-weight:800;font-size:1.2rem;color:#e9e6dd;text-align:center}
.aprow2 img{width:26px;height:26px;object-fit:contain}
.aprow2 .tm{font-weight:700;color:#eae7e0}
.aprow2 .tm small{display:block;color:#8489b4;font-weight:500;font-size:.72rem}
.aprow2 .pi{text-align:center;font-size:.72rem;color:#8489b4}
.aprow2 .pi b{color:#c8aa6e;font-size:.9rem}
.aphead{display:grid;grid-template-columns:40px 32px 1fr 60px 44px;gap:12px;padding:6px 14px;
  font-size:.62rem;letter-spacing:1px;color:#6a7094;text-transform:uppercase;font-weight:700;
  border-bottom:1px solid rgba(255,255,255,.1)}

/* segmented / pill radios — top nav + in-page toggles read as one system */
div[role="radiogroup"]{gap:6px;flex-wrap:wrap}
div[role="radiogroup"] > label{
  background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);
  border-radius:9px;padding:7px 15px;margin:0!important;cursor:pointer;transition:all .15s}
div[role="radiogroup"] > label:hover{border-color:rgba(200,170,110,.45)}
div[role="radiogroup"] > label > div:first-child{display:none!important}   /* hide the dot */
div[role="radiogroup"] > label:has(input:checked){
  background:rgba(200,170,110,.15);border-color:#c8aa6e}
div[role="radiogroup"] > label:has(input:checked) p{color:#e9d9ab!important}
div[role="radiogroup"] p{font-weight:600;font-size:.84rem;color:#9a9eb8}
.navmark + div [role="radiogroup"]{margin-bottom:6px;padding-bottom:10px;
  border-bottom:1px solid rgba(255,255,255,.08)}

/* playoff bracket */
.bgame{display:flex;align-items:center;gap:10px;background:rgba(255,255,255,.022);
  border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:10px 14px;margin-bottom:9px}
.bgame.bye{opacity:.92;border-color:rgba(200,170,110,.25)}
.bvs{color:#5a5e7a;font-size:.66rem;font-weight:800;letter-spacing:1.5px;min-width:28px;text-align:center}
.bteam{display:flex;align-items:center;gap:9px;flex:1;min-width:0}
.bteam.ph{color:#5a5e7a}
.bteam img{width:30px;height:30px;object-fit:contain}
.bteam .bseed{font-family:'Playfair Display',serif;font-weight:800;color:#c8aa6e;
  font-size:1rem;min-width:20px;text-align:center}
.bteam .bnm{font-weight:700;color:#eae7e0;font-size:.9rem;line-height:1.15;overflow:hidden}
.bteam .bnm small{display:block;color:#8489b4;font-weight:500;font-size:.68rem}

/* click-anywhere team links — any logo/name/row that wraps in .tlink */
a.tlink{display:block;text-decoration:none;color:inherit;border-radius:10px;
  transition:background .12s,transform .12s}
a.tlink:hover{background:rgba(200,170,110,.09)}
a.tlink:hover .tm,a.tlink:hover .nm,a.tlink:hover .bnm{color:#f0d898!important}
a.tlink .mt{cursor:pointer}
.clickhint{font-size:.7rem;color:#6a7094;margin:2px 0 6px}
.clickhint b{color:#c8aa6e}

/* themed buttons — match the gold/dark system */
.stButton>button{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.1);
  color:#c8cbd8;border-radius:9px;font-weight:600;font-size:.8rem;transition:all .15s}
.stButton>button:hover{border-color:#c8aa6e;color:#e9d9ab;background:rgba(200,170,110,.1)}
.stButton>button:active{transform:translateY(1px)}

/* team-colored accent on matchup cards */
.mcard{border-left:3px solid var(--fav,rgba(200,170,110,.4))}

/* dataframe container — softer frame that blends with the dark theme */
[data-testid="stDataFrame"]{border:1px solid rgba(255,255,255,.07);border-radius:12px;overflow:hidden}
[data-testid="stExpander"] summary:hover{color:#e2c78a}
</style>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB: LIVE 2026  (AP poll, best matchups, scoreboard, live standings, FPI)
# ══════════════════════════════════════════════════════════════════════════════
if page == PAGE_LIVE:
    ch1, ch2 = st.columns([5, 1])
    with ch1:
        st.markdown('<div class="livehdr"><span class="livedot"></span>'
                    '<h3 style="margin:0">Live 2026 Season</h3></div>', unsafe_allow_html=True)
    with ch2:
        if st.button("↻ Refresh", key="live_refresh", use_container_width=True):
            L.clear_live_cache(); st.rerun()

    with st.spinner("Pulling live data from ESPN…"):
        ap = L.get_ap_top25()
        sb = L.get_scoreboard()
        standings = L.get_standings()
        fpi = L.get_fpi()

    if ap.empty and sb.empty and standings.empty:
        st.error("Couldn't reach ESPN right now. Live data is fetched at runtime — "
                 "try the Refresh button in a moment. Preseason tabs still work.")
    else:
        wk = sb.attrs.get("week") or ap.attrs.get("week") or ""
        st.caption(f"AP Top 25 · Scoreboard · Standings · FPI — live from ESPN · Week {wk} · 2026")

        # ── Jump straight to any team's page ────────────────────────────────────
        def _jump():
            v = st.session_state.get("live_jump")
            if v and v != "— open any team's page —":
                st.session_state["_goto_team"] = v
        st.selectbox("Open a team", ["— open any team's page —"] + FBS_LIST,
                     key="live_jump", on_change=_jump, label_visibility="collapsed")

        # ── This week's best matchups (click either team to open its page) ───────
        bm = L.best_matchups(sb, 6)
        if not bm.empty:
            st.markdown("#### 🔥 This Week's Best Matchups")
            st.markdown('<div class="clickhint">Click <b>any team</b> to open its page.</div>',
                        unsafe_allow_html=True)
            cols = st.columns(3)
            for i, g in enumerate(bm.itertuples()):
                c = cols[i % 3]
                hr = f'<span class="rk">#{int(g.home_rank)}</span>' if pd.notna(g.home_rank) and g.home_rank else ''
                ar = f'<span class="rk">#{int(g.away_rank)}</span>' if pd.notna(g.away_rank) and g.away_rank else ''
                try:
                    when = pd.to_datetime(g.date).strftime("%a %-I:%M %p")
                except Exception:
                    when = str(g.status)
                spread = f"<b>{esc(g.spread)}</b>" if g.spread else "—"
                # accent card in the favorite's color (home team as a simple proxy)
                fav = team_color(espn_to_school(g.home))
                away_row = team_link(g.away, f'<div class="mt"><img src="{g.away_logo}">'
                    f'<span class="nm">{esc(g.away)}</span> {ar}'
                    f'<span class="rec" style="color:#5a5e7a;font-size:.72rem;margin-left:auto">{esc(g.away_rec)}</span></div>')
                home_row = team_link(g.home, f'<div class="mt"><img src="{g.home_logo}">'
                    f'<span class="nm">{esc(g.home)}</span> {hr}'
                    f'<span class="rec" style="color:#5a5e7a;font-size:.72rem;margin-left:auto">{esc(g.home_rec)}</span></div>')
                c.markdown(f"""<div class="mcard" style="--fav:{fav}">
                  {away_row}<div class="vs">AT</div>{home_row}
                  <div class="meta"><span>{esc(when)} · {esc(g.tv or "TV TBD")}</span><span>{spread}</span></div>
                </div>""", unsafe_allow_html=True)
            st.write("")

        # ── Live 2026 stat leaders ───────────────────────────────────────────────
        leaders = L.get_stat_leaders()
        if leaders:
            st.markdown("#### 📈 2026 Stat Leaders")
            id2name = dict(zip(FBS_TEAMS["team_id"].astype(str), FBS_TEAMS["team"])) \
                if not FBS_TEAMS.empty else {}
            lc = st.columns(len(leaders))
            for i, ld in enumerate(leaders):
                tname = id2name.get(str(ld["team_id"]), "")
                logo = f'<img src="{ld["logo"]}" style="width:22px;height:22px;object-fit:contain;vertical-align:middle;margin-right:5px">' if ld["logo"] else ""
                inner = (f'<div class="kpi" style="text-align:left">'
                         f'<div class="lbl">{esc(ld["cat"])}</div>'
                         f'<div class="val" style="font-size:1.5rem">{esc(ld["value"])}</div>'
                         f'<div class="sub">{logo}{esc(ld["player"])}</div></div>')
                lc[i].markdown(team_link(tname, inner) if tname else inner,
                               unsafe_allow_html=True)
            st.write("")

        cA, cB = st.columns([3, 4])

        # ── AP Top 25 (dark, on-theme, with my preseason rank) ──────────────────
        with cA:
            st.markdown("#### 🏆 AP Top 25")
            if ap.empty:
                st.info("AP poll unavailable right now.")
            else:
                rows_html = ['<div class="card" style="padding:6px 0 2px">',
                             '<div class="aphead"><span>#</span><span></span><span>Team</span>'
                             '<span style="text-align:center">Rec</span>'
                             '<span style="text-align:center">My PI</span></div>']
                for r in ap.itertuples():
                    prk = preseason_rank(r.team)
                    pit = f'<b>#{prk}</b>' if prk else '—'
                    fpv = f' · {int(r.fpv)} 1st' if getattr(r, "fpv", 0) else ''
                    row = (
                        f'<div class="aprow2"><span class="r">{r.rank}</span>'
                        f'<img src="{r.logo}">'
                        f'<span class="tm">{esc(r.team)} {trend_chip(r.trend)}'
                        f'<small>{int(r.points):,} pts{fpv}</small></span>'
                        f'<span class="pi" style="color:#8489b4">{esc(r.record)}</span>'
                        f'<span class="pi">{pit}</span></div>')
                    rows_html.append(team_link(r.team, row))
                rows_html.append('</div>')
                st.markdown("".join(rows_html), unsafe_allow_html=True)
                st.markdown('<div class="clickhint">Click <b>any team</b> to open its page · '
                            '<b>My PI</b> = my preseason model rank (voters vs model)</div>',
                            unsafe_allow_html=True)

        # ── Live standings / FPI ───────────────────────────────────────────────
        with cB:
            sub = st.radio("View", ["Conference Standings", "ESPN FPI (power ratings)"],
                           horizontal=True, key="live_sub", label_visibility="collapsed")
            if sub == "Conference Standings" and not standings.empty:
                confs = sorted(standings["conf"].dropna().unique().tolist())
                default = confs.index("SEC") if "SEC" in confs else 0
                pick = st.selectbox("Conference", confs, index=default, key="live_conf")
                cs = standings[standings["conf"] == pick].copy()
                cs = cs.sort_values(["win_pct", "wins"], ascending=False)
                cs["My PI"] = cs["team"].map(lambda t: preseason_rank(t))
                st.dataframe(
                    cs[["logo", "team", "overall", "conf_rec", "My PI"]],
                    hide_index=True, use_container_width=True, height=520,
                    column_config={
                        "logo": st.column_config.ImageColumn("", width="small"),
                        "team": st.column_config.TextColumn("Team"),
                        "overall": st.column_config.TextColumn("Overall", width="small"),
                        "conf_rec": st.column_config.TextColumn("Conf", width="small"),
                        "My PI": st.column_config.NumberColumn("My PI", width="small"),
                    })
            elif not fpi.empty:
                fcol = "fpi" if "fpi" in fpi.columns else fpi.columns[3]
                rcol = "fpirank" if "fpirank" in fpi.columns else None
                fv = fpi.copy()
                if rcol: fv = fv.sort_values(rcol)
                else: fv = fv.sort_values(fcol, ascending=False)
                fv["My PI"] = fv["team"].map(lambda t: preseason_rank(t))
                keep = {"fpirank": "FPI Rk", "team": "Team", "fpi": "FPI",
                        "projectedw": "Proj W", "projectedl": "Proj L",
                        "probmakeplayoffs": "Playoff %", "My PI": "My PI"}
                cols_present = [c for c in keep if c in fv.columns]
                disp = fv[cols_present + (["My PI"] if "My PI" not in cols_present else [])].head(30).rename(columns=keep)
                if "Playoff %" in disp.columns:
                    disp["Playoff %"] = (pd.to_numeric(disp["Playoff %"], errors="coerce")).round(1)
                for c in ["FPI", "Proj W", "Proj L"]:
                    if c in disp.columns: disp[c] = pd.to_numeric(disp[c], errors="coerce").round(1)
                st.dataframe(disp, hide_index=True, use_container_width=True, height=520)
                st.caption("ESPN's Football Power Index — a live, forward-looking power rating "
                           "(projected wins, playoff odds). Good external check on my model.")
            else:
                st.info("Standings/FPI unavailable right now.")

        # ── Full scoreboard ────────────────────────────────────────────────────
        if not sb.empty:
            with st.expander(f"📋 Full Week {wk} scoreboard — all {len(sb)} games"):
                sv = sb.copy()
                def _score(r):
                    if r["completed"] and r["home_score"] is not None:
                        return f"{r['away']} {r['away_score']} — {r['home_score']} {r['home']}"
                    return r["status"]
                sv["matchup"] = sv.apply(
                    lambda r: f"{'#'+str(int(r['away_rank']))+' ' if pd.notna(r['away_rank']) and r['away_rank'] else ''}{r['away']} "
                              f"@ {'#'+str(int(r['home_rank']))+' ' if pd.notna(r['home_rank']) and r['home_rank'] else ''}{r['home']}", axis=1)
                sv["result / time"] = sv.apply(_score, axis=1)
                st.dataframe(sv[["matchup", "result / time", "spread", "tv", "venue"]],
                             hide_index=True, use_container_width=True, height=460,
                             column_config={"matchup": "Matchup", "result / time": "Result / Time",
                                            "spread": "Line", "tv": "TV", "venue": "Venue"})

# ══════════════════════════════════════════════════════════════════════════════
# TAB: TEAM 2026  (live per-team: record, stats, schedule, SOS, roster, blend)
# ══════════════════════════════════════════════════════════════════════════════
if page == PAGE_TEAM:
    fbs = L.get_fbs_teams()
    if fbs.empty:
        st.error("Couldn't reach ESPN to load the team list. Try again in a moment (runtime fetch).")
    else:
        names = fbs["team"].tolist()
        if "live_team" not in st.session_state or st.session_state["live_team"] not in names:
            st.session_state["live_team"] = "Texas" if "Texas" in names else names[0]
        cpick1, cpick2 = st.columns([5, 1])
        with cpick1:
            pick = st.selectbox("Select team", names, key="live_team")
        with cpick2:
            st.write(""); st.write("")
            if st.button("↻ Refresh", key="team_refresh", use_container_width=True):
                L.clear_live_cache(); st.rerun()
        trow = fbs[fbs["team"] == pick].iloc[0]
        tid = trow["team_id"]

        with st.spinner(f"Loading {pick}'s 2026 season…"):
            standings = L.get_standings()
            sched = L.get_team_schedule(tid)
            roster = L.get_team_roster(tid)
            fpi = L.get_fpi()
            ap = L.get_ap_top25()

        srow = standings[standings["team_id"] == tid]
        overall = srow.iloc[0]["overall"] if not srow.empty else "—"
        cur_w = int(srow.iloc[0]["wins"]) if not srow.empty and pd.notna(srow.iloc[0]["wins"]) else 0
        cur_l = int(srow.iloc[0]["losses"]) if not srow.empty and pd.notna(srow.iloc[0]["losses"]) else 0
        conf = srow.iloc[0]["conf"] if not srow.empty else ""
        frow = fpi[fpi["team_id"] == tid]
        aprow = ap[ap["team_id"] == tid]
        ap_rk = int(aprow.iloc[0]["rank"]) if not aprow.empty else None
        pre_rk = preseason_rank(pick)
        sc = espn_to_school(pick)
        cc = team_color(sc)

        # ── Banner ─────────────────────────────────────────────────────────────
        rank_badge = f'<div class="bigrank">#{ap_rk}</div>' if ap_rk else ''
        st.markdown(f"""<div class="tbanner" style="--c1:{cc}">
          <div style="display:flex;align-items:center;gap:16px">
            <img src="{trow['logo']}" style="width:64px;height:64px;object-fit:contain">
            <div><div class="tname">{esc(pick)}</div>
            <div class="tmeta">{esc(conf)} · {esc(overall)} in 2026{' · AP #'+str(ap_rk) if ap_rk else ''}</div></div>
          </div>{rank_badge}
        </div>""", unsafe_allow_html=True)

        # ── KPI row ────────────────────────────────────────────────────────────
        def _f(col):
            if frow.empty or col not in frow.columns: return None
            return pd.to_numeric(frow.iloc[0][col], errors="coerce")
        fpi_rk = _f("fpirank"); fpi_val = _f("fpi")
        pw, pl = _f("projectedw"), _f("projectedl")
        po = _f("probmakeplayoffs"); sos_rk = _f("avgsosrank")
        k = st.columns(6)
        def kpi(col, lbl, val, sub=""):
            col.markdown(f'<div class="kpi"><div class="lbl">{lbl}</div>'
                         f'<div class="val">{val}</div><div class="sub">{sub}</div></div>',
                         unsafe_allow_html=True)
        kpi(k[0], "AP Rank", f"#{ap_rk}" if ap_rk else "NR", "national poll")
        kpi(k[1], "FPI Rank", f"#{int(fpi_rk)}" if pd.notna(fpi_rk) else "—", "ESPN power")
        kpi(k[2], "FPI Rating", f"{fpi_val:.1f}" if pd.notna(fpi_val) else "—", "pts vs avg")
        kpi(k[3], "ESPN Proj", f"{pw:.0f}-{pl:.0f}" if pd.notna(pw) else "—", "full-season")
        kpi(k[4], "Playoff Odds", f"{po:.0f}%" if pd.notna(po) else "—", "make CFP (FPI)")
        kpi(k[5], "My Preseason", f"#{pre_rk}" if pre_rk else "—", "my Power Index")

        st.write("")
        colL, colR = st.columns([3, 2])

        # ── Schedule ───────────────────────────────────────────────────────────
        with colL:
            st.markdown("#### 2026 Schedule & Results")
            if sched.empty:
                st.info("Schedule unavailable.")
            else:
                for g in sched.itertuples():
                    ha = "vs" if g.home_away == "home" else "@"
                    orank = f'<span style="color:#c8aa6e;font-weight:800">#{int(g.opp_rank)}</span> ' \
                            if pd.notna(g.opp_rank) and g.opp_rank and g.opp_rank <= 25 else ''
                    if g.completed and g.result:
                        cls = "win" if g.result == "W" else ("loss" if g.result == "L" else "")
                        pf = int(g.pts_for) if pd.notna(g.pts_for) else ""
                        pa = int(g.pts_against) if pd.notna(g.pts_against) else ""
                        right = f'<span class="gsc {cls}">{g.result} {pf}-{pa}</span>'
                    else:
                        when = ""
                        try: when = pd.to_datetime(g.date).strftime("%b %-d")
                        except Exception: when = ""
                        right = f'<span style="color:#8489b4;font-size:.78rem">{esc(when)}</span>'
                    hc = "home" if g.home_away == "home" else ""
                    st.markdown(f"""<div class="schrow {hc}" style="grid-template-columns:44px 1fr 90px">
                      <span class="wk">WK {g.week if pd.notna(g.week) else '—'}</span>
                      <span class="opp"><img src="{g.opp_logo}" style="width:20px;height:20px;object-fit:contain;vertical-align:middle;margin-right:6px">
                        {ha} {orank}{esc(g.opp)}</span>
                      <span style="text-align:right">{right}</span>
                    </div>""", unsafe_allow_html=True)

        # ── Strength of schedule + model-vs-reality ─────────────────────────────
        with colR:
            st.markdown("#### Strength of Schedule")
            sos = L.strength_of_schedule(sched, standings)
            s1, s2, s3 = st.columns(3)
            kpi(s1, "Played", f"{sos['played']:.0f}" if sos['played'] is not None else "—", "opp win%·100")
            kpi(s2, "Remaining", f"{sos['remaining']:.0f}" if sos['remaining'] is not None else "—", "road ahead")
            kpi(s3, "Full Slate", f"{sos['full']:.0f}" if sos['full'] is not None else "—",
                f"ESPN SOS #{int(sos_rk)}" if pd.notna(sos_rk) else "0-100")
            if sos["hardest_ahead"]:
                st.markdown("**Toughest games remaining**")
                for nm, wpct, rk in sos["hardest_ahead"]:
                    rks = f' · #{int(rk)}' if rk and rk <= 25 else ''
                    st.markdown(f'<div class="pcard-line">🔺 <b style="color:#eae7e0">{esc(nm)}</b>'
                                f'<span style="color:#8489b4;margin-left:auto">{wpct}% win{rks}</span></div>',
                                unsafe_allow_html=True)
            st.write("")
            st.markdown("#### Model vs Reality")
            insight = f"My preseason model ranked **{esc(pick)}** "
            insight += f"**#{pre_rk}**. " if pre_rk else "outside the FBS set. "
            if ap_rk and pre_rk:
                d = pre_rk - ap_rk
                if d > 5: insight += f"They're **outperforming** it — up to AP #{ap_rk} (+{d})."
                elif d < -5: insight += f"They're **underperforming** it — down to AP #{ap_rk} ({d})."
                else: insight += f"AP has them #{ap_rk} — right where the model expected."
            elif ap_rk:
                insight += f"Voters now have them AP #{ap_rk}."
            st.markdown(f'<div class="note">{md_b(insight)}</div>', unsafe_allow_html=True)

        # ═══════════════════════════════════════════════════════════════════════
        # REST-OF-SEASON PREDICTOR  (blended: ESPN FPI + my model + SOS + HFA)
        # ═══════════════════════════════════════════════════════════════════════
        st.markdown("---")
        st.markdown("### 🔮 Rest-of-Season Predictor")
        st.caption("One power rating per team = **65% ESPN FPI** (live form) + **35% my preseason "
                   "Power Index** (returning production, QB, transfers, coaching, schedule), then every "
                   "remaining game is simulated with a home-field edge. Updates live each week.")

        # Fixed, tuned parameters (kept simple — no knobs to fiddle).
        blend = 0.65   # weight on live FPI vs my preseason model
        hfa = 2.4      # home-field edge in points

        # Build a points-scale rating per ESPN team_id from FPI and my index.
        fpi_std = 12.0
        fpi_by_id = {}
        if not fpi.empty:
            fv = pd.to_numeric(fpi["fpi"], errors="coerce")
            fpi_std = float(fv.std()) or 12.0
            fpi_by_id = {str(i): v for i, v in zip(fpi["team_id"], fv) if pd.notna(v)}
        # my rating: map ESPN id -> location (fbs) -> School -> team_strength_rating
        my_by_id = {}
        if has_v2 and "team_strength_rating" in v2.columns:
            tsr_mean = float(v2["team_strength_rating"].mean())
            tsr_std = float(v2["team_strength_rating"].std()) or 1.0
            school_tsr = dict(zip(v2["School"], v2["team_strength_rating"]))
            for _, fr in fbs.iterrows():
                s2 = espn_to_school(fr["team"])
                if s2 in school_tsr:
                    z = (school_tsr[s2] - tsr_mean) / tsr_std
                    my_by_id[str(fr["team_id"])] = z * fpi_std  # onto points scale

        def rating(team_id):
            i = str(team_id)
            f = fpi_by_id.get(i)
            m = my_by_id.get(i)
            if f is not None and m is not None:
                return blend * f + (1 - blend) * m
            if f is not None: return f
            if m is not None: return m
            return -18.0  # FCS / unrated opponent

        my_rating = rating(tid)
        remaining = sched[~sched["completed"]] if not sched.empty else pd.DataFrame()
        exp_wins = 0.0
        pred_rows = []
        for g in remaining.itertuples():
            opp_r = rating(g.opp_id)
            edge = (hfa if g.home_away == "home" else (-hfa if g.home_away == "away" else 0))
            spread = my_rating - opp_r + edge
            wp = L.win_prob(spread)
            exp_wins += wp
            pred_rows.append({
                "Wk": g.week, "Opp": g.opp, "Loc": "Home" if g.home_away == "home" else
                ("Away" if g.home_away == "away" else "Neutral"),
                "Proj margin": round(spread, 1), "Win %": round(wp * 100)})

        proj_w = cur_w + exp_wins
        proj_l = cur_l + (len(remaining) - exp_wins)
        m1, m2, m3, m4 = st.columns(4)
        kpi(m1, "Current", f"{cur_w}-{cur_l}", "actual")
        kpi(m2, "Proj Final", f"{proj_w:.1f}-{proj_l:.1f}", "expected value")
        kpi(m3, "Games Left", f"{len(remaining)}", "to simulate")
        kpi(m4, "My Rating", f"{my_rating:+.1f}", f"pts vs avg · blend")

        if pred_rows:
            pdf = pd.DataFrame(pred_rows)
            st.dataframe(
                pdf, hide_index=True, use_container_width=True,
                height=min(460, len(pdf) * 38 + 40),
                column_config={
                    "Wk": st.column_config.NumberColumn("Wk", width="small"),
                    "Opp": st.column_config.TextColumn("Opponent"),
                    "Loc": st.column_config.TextColumn("Site", width="small"),
                    "Proj margin": st.column_config.NumberColumn("Proj Margin", format="%+.1f",
                        help="Projected points margin (+ = favored)"),
                    "Win %": st.column_config.ProgressColumn("Win Probability", min_value=0,
                        max_value=100, format="%d%%"),
                })
            st.caption(f"Expected additional wins: **{exp_wins:.1f}** of {len(remaining)} remaining. "
                       "Margin = blended rating gap + home-field edge; win% via a normal model (σ=16.5).")
        else:
            st.info("No remaining games to project — season complete.")

        # what drives OUR rating (coaching / transfer / SOS / QB / returning)
        if has_v2 and sc in set(v2["School"]):
            vr = v2[v2["School"] == sc].iloc[0]
            drivers = [("QB Room", "qb_score"), ("Returning Prod", "returning_production_score"),
                       ("Portal Net", "transfer_impact_score"), ("Recruiting", "recruiting_talent_score"),
                       ("Coaching", "coaching_continuity_score"), ("Schedule", "schedule_strength_score")]
            have = [(lbl, float(vr[c])) for lbl, c in drivers if c in v2.columns and pd.notna(vr[c])]
            if have:
                with st.expander("⚙️ What drives MY rating for this team (0–100 components)"):
                    dfig = go.Figure()
                    have_sorted = sorted(have, key=lambda x: x[1])
                    dfig.add_trace(go.Bar(
                        y=[l for l, _ in have_sorted], x=[v for _, v in have_sorted],
                        orientation="h",
                        marker=dict(color=[GREEN if v >= 65 else (RED if v < 48 else GOLD)
                                           for _, v in have_sorted]),
                        text=[f"{v:.0f}" for _, v in have_sorted], textposition="outside"))
                    dfig.update_layout(**PL, height=260, xaxis=dict(range=[0, 110]),
                                       showlegend=False, margin=dict(l=10, r=30, t=10, b=10))
                    sf(dfig); st.plotly_chart(dfig, use_container_width=True)

        # ═══════════════════════════════════════════════════════════════════════
        # SEASON STATS  (2026 default, 2025 optional — both live from ESPN)
        # ═══════════════════════════════════════════════════════════════════════
        st.markdown("---")
        sh1, sh2 = st.columns([3, 1])
        with sh1:
            st.markdown("### 📊 Team Stats")
        with sh2:
            season = st.selectbox("Season", [2026, 2025], index=0, key="stat_season")
        tstats = L.get_team_stats(tid, season)

        def sval(cat, display):
            b = tstats.get(cat, {})
            for kk, vv in b.items():
                if kk.lower() == display.lower():
                    return vv.get("value")
            for kk, vv in b.items():
                if display.lower() in kk.lower():
                    return vv.get("value")
            return None

        def _num(x):
            try: return float(str(x).replace(",", ""))
            except Exception: return None

        if not tstats:
            st.info(f"No {season} team stats posted yet.")
        else:
            gp = _num(sval("rushing", "Team Games Played") or sval("scoring", "Team Games Played")) or 1
            off = [
                ("Points / Game", sval("scoring", "Total Points Per Game")),
                ("Total Yds / Game", None),
                ("Pass Yds / Game", sval("passing", "Net Passing Yards Per Game")),
                ("Rush Yds / Game", sval("rushing", "Rushing Yards Per Game")),
                ("Yds / Pass", sval("passing", "Yards Per Pass Attempt")),
                ("Yds / Rush", sval("rushing", "Yards Per Rush Attempt")),
            ]
            tot_yds = _num(sval("rushing", "Total Yards") or sval("passing", "Total Yards"))
            plays = _num(sval("rushing", "Total Offensive Plays"))
            if tot_yds:
                off[1] = ("Total Yds / Game", round(tot_yds / gp, 1))
            st.markdown("**Offense**")
            oc = st.columns(len(off))
            for i, (lbl, val) in enumerate(off):
                oc[i].markdown(f'<div class="kpi"><div class="lbl">{lbl}</div>'
                               f'<div class="val" style="font-size:1.3rem">{esc(val) if val is not None else "—"}</div>'
                               f'<div class="sub">{int(gp)} gm</div></div>', unsafe_allow_html=True)
            deff = [
                ("Sacks", sval("defensive", "Sacks")),
                ("TFL", sval("defensive", "Tackles For Loss")),
                ("Total Tackles", sval("defensive", "Total Tackles")),
                ("Interceptions", sval("defensiveInterceptions", "Interceptions") or sval("defensive", "Interceptions")),
                ("Fumbles Rec", sval("general", "Fumbles Recovered")),
                ("Yds / Play", round(tot_yds / plays, 1) if tot_yds and plays else None),
            ]
            st.markdown("**Defense & efficiency**")
            dc = st.columns(len(deff))
            for i, (lbl, val) in enumerate(deff):
                dc[i].markdown(f'<div class="kpi"><div class="lbl">{lbl}</div>'
                               f'<div class="val" style="font-size:1.3rem">{esc(val) if val is not None else "—"}</div>'
                               f'<div class="sub">{season}</div></div>', unsafe_allow_html=True)

        # ═══════════════════════════════════════════════════════════════════════
        # DEPTH CHART  (field-style, live 2026 roster)
        # ═══════════════════════════════════════════════════════════════════════
        st.markdown("---")
        st.markdown("### 🏈 Depth Chart  ·  live 2026 roster")
        if roster.empty:
            st.info("Roster unavailable right now.")
        else:
            def cls_badge(cl):
                return {"FR": "b", "SO": "g", "JR": "y", "SR": "r"}.get(str(cl).upper(), "")

            def rchip(r):
                badge = cls_badge(r.cls)
                cl = esc(r.cls) if str(r.cls) not in ("nan", "None", "") else ""
                return (f'<div class="pchip"><div class="pos">#{esc(r.jersey)} · {esc(r.pos)}</div>'
                        f'<div class="name">{esc(r.name)}</div>'
                        f'<div class="pstat">{esc(r.height)} · {esc(r.weight)}</div>'
                        f'<div class="tag"><span class="chip {badge}">{cl}</span></div></div>')

            _ros = roster.rename(columns={"class": "cls"})
            # Known 2026 starting QB (from curated QB data) surfaced first at QB.
            _qbrow = qbs_df[qbs_df["team"] == sc] if not qbs_df.empty else pd.DataFrame()
            _starter_qb = str(_qbrow.iloc[0]["qb"]).strip() if not _qbrow.empty else ""
            _sq_last = _starter_qb.split()[-1].lower() if _starter_qb else ""

            def take(poss, n):
                sub = _ros[_ros["pos"].isin(poss)]
                rows = list(sub.itertuples())
                if "QB" in poss and _sq_last:  # float the known starter to the top
                    rows.sort(key=lambda r: 0 if _sq_last in str(r.name).lower() else 1)
                return rows[:n]

            def frow(items):
                return ('<div class="frow">' + "".join(rchip(r) for r in items) + '</div>') if items else ''

            off = (f'<div class="fieldcol"><div class="fieldttl">Offense</div>'
                   f'<div class="field" style="--c1:{cc}"><div class="endzone">{esc(pick)}</div>'
                   f'{frow(take(["WR"],3)+take(["TE"],1))}'
                   f'{frow(take(["QB"],1)+take(["RB","FB"],1))}'
                   f'{frow(take(["OT","OG","C","OL","G","T","IOL"],5))}'
                   f'</div></div>')
            dfe = (f'<div class="fieldcol"><div class="fieldttl">Defense</div>'
                   f'<div class="field" style="--c1:{cc}"><div class="endzone">Defense</div>'
                   f'{frow(take(["DE","DT","DL","NT","EDGE"],4))}'
                   f'{frow(take(["LB","ILB","OLB","MLB"],3))}'
                   f'{frow(take(["CB","DB"],2)+take(["S","SS","FS"],2))}'
                   f'</div></div>')
            st.markdown(f'<div class="fieldwrap">{off}{dfe}</div>', unsafe_allow_html=True)
            st.caption("Live 2026 roster, grouped by unit (ESPN doesn't publish an official two-deep, "
                       "so within a group players are listed alphabetically — the projected starting QB "
                       "is floated first). Class badges: "
                       "<span class='chip b'>FR</span> <span class='chip g'>SO</span> "
                       "<span class='chip y'>JR</span> <span class='chip r'>SR</span>",
                       unsafe_allow_html=True)

            with st.expander(f"📋 Full roster — {len(roster)} players (searchable)"):
                q = st.text_input("Filter by name or position", "", key="roster_filter")
                rr = roster.copy()
                if q:
                    rr = rr[rr["name"].str.contains(q, case=False, na=False) |
                            rr["pos"].str.contains(q, case=False, na=False)]
                st.dataframe(rr[["jersey", "name", "pos", "class", "height", "weight", "hometown"]],
                             hide_index=True, use_container_width=True, height=460,
                             column_config={"jersey": st.column_config.TextColumn("#", width="small"),
                                            "name": "Name", "pos": st.column_config.TextColumn("Pos", width="small"),
                                            "class": st.column_config.TextColumn("Cl", width="small"),
                                            "height": st.column_config.TextColumn("Ht", width="small"),
                                            "weight": st.column_config.TextColumn("Wt", width="small"),
                                            "hometown": "Hometown"})

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: PLAYOFF PREDICTOR  (projected 12-team CFP field + bracket + odds)
# ══════════════════════════════════════════════════════════════════════════════
if page == PAGE_CFP:
    c1, c2 = st.columns([5, 1])
    with c1:
        st.markdown("### 🏆 College Football Playoff Predictor")
    with c2:
        if st.button("↻ Refresh", key="cfp_refresh", use_container_width=True):
            L.clear_live_cache(); st.rerun()
    st.caption("Projected 12-team field — **5 highest-rated conference champions** get auto bids, "
               "then the **7 best at-large** teams; all straight-seeded. Odds combine **ESPN FPI** "
               "(its full-season simulation) with a Monte-Carlo run of the actual bracket off my "
               "blended power rating (FPI + returning production, QB, transfers, coaching, schedule).")

    with st.spinner("Building the bracket from live ratings…"):
        pr = power_ratings()
        field = project_cfp_field(pr)
        field = simulate_bracket(field, n=4000) if not field.empty else field

    if field is None or field.empty:
        st.error("Couldn't reach ESPN to build the field right now. Try Refresh in a moment.")
    else:
        proj_champ = field.sort_values("p_title", ascending=False).iloc[0]
        st.markdown(
            f'<div class="tbanner" style="--c1:{team_color(espn_to_school(proj_champ["name"]))}">'
            f'<div style="display:flex;align-items:center;gap:16px">'
            f'<img src="{proj_champ["logo"]}" style="width:60px;height:60px;object-fit:contain">'
            f'<div><div class="tmeta" style="opacity:.85">PROJECTED NATIONAL CHAMPION</div>'
            f'<div class="tname">{esc(proj_champ["name"])}</div>'
            f'<div class="tmeta">{proj_champ["p_title"]:.0f}% to win it all · '
            f'#{int(proj_champ["seed"])} seed · {esc(str(proj_champ.get("record","")))}</div></div></div>'
            f'</div>', unsafe_allow_html=True)

        # ── Bracket view ────────────────────────────────────────────────────────
        st.markdown("#### Projected Bracket")
        byes = field[field["seed"] <= 4]
        r1 = [(5, 12), (6, 11), (7, 10), (8, 9)]

        def seed_cell(seed):
            row = field[field["seed"] == seed]
            if row.empty: return '<div class="bteam ph">—</div>'
            r = row.iloc[0]
            ac = ' · <span style="color:#c8aa6e">conf champ</span>' if r["auto"] else ''
            cell = (f'<div class="bteam"><img src="{r["logo"]}">'
                    f'<span class="bseed">{int(r["seed"])}</span>'
                    f'<span class="bnm">{esc(r["name"])}<small>{esc(str(r.get("record","")))}'
                    f' · {r["p_title"]:.0f}% title{ac}</small></span></div>')
            return team_link(r["name"], cell)

        bl, br = st.columns(2)
        with bl:
            st.markdown('<div class="fieldttl">First round — home site is higher seed</div>',
                        unsafe_allow_html=True)
            for hi, lo in r1:
                st.markdown(f'<div class="bgame">{seed_cell(hi)}'
                            f'<div class="bvs">vs</div>{seed_cell(lo)}</div>',
                            unsafe_allow_html=True)
        with br:
            st.markdown('<div class="fieldttl">Top 4 seeds — first-round bye</div>',
                        unsafe_allow_html=True)
            for s in range(1, 5):
                st.markdown(f'<div class="bgame bye">{seed_cell(s)}'
                            f'<div class="bvs">BYE</div></div>', unsafe_allow_html=True)

        # ── Odds table (my sim + ESPN FPI) ──────────────────────────────────────
        st.markdown("#### Championship Odds")
        view = st.radio("Pool", ["Projected 12-team field", "All contenders"],
                        horizontal=True, key="cfp_view", label_visibility="collapsed")
        base = field if view.startswith("Projected") else pr.head(30).copy()
        if "seed" not in base.columns: base["seed"] = None
        # attach FPI odds
        for col in ["probmakeplayoffs", "probwinconf", "probwintitle"]:
            if col not in base.columns: base[col] = np.nan
        tbl = base.copy()
        tbl["Seed"] = tbl["seed"]
        tbl["FPI Make CFP %"] = pd.to_numeric(tbl.get("probmakeplayoffs"), errors="coerce").round(1)
        tbl["FPI Title %"] = pd.to_numeric(tbl.get("probwintitle"), errors="coerce").round(1)
        show_cols = ["Seed", "logo", "name", "conf", "record"]
        my_cols = [c for c in ["p_f4", "p_final", "p_title"] if c in tbl.columns]
        ren = {"logo": "", "name": "Team", "conf": "Conf", "record": "Rec",
               "p_f4": "My Final 4 %", "p_final": "My Final %", "p_title": "My Title %"}
        disp = tbl[show_cols + my_cols + ["FPI Make CFP %", "FPI Title %"]].rename(columns=ren)
        st.dataframe(
            disp, hide_index=True, use_container_width=True, height=min(560, len(disp) * 36 + 44),
            column_config={
                "Seed": st.column_config.NumberColumn("Seed", width="small"),
                "": st.column_config.ImageColumn("", width="small"),
                "Team": st.column_config.TextColumn("Team"),
                "Conf": st.column_config.TextColumn("Conf", width="small"),
                "Rec": st.column_config.TextColumn("Rec", width="small"),
                "My Final 4 %": st.column_config.ProgressColumn("My Final 4 %", min_value=0, max_value=100, format="%d%%"),
                "My Final %": st.column_config.ProgressColumn("My Final %", min_value=0, max_value=100, format="%d%%"),
                "My Title %": st.column_config.ProgressColumn("My Title %", min_value=0, max_value=100, format="%d%%"),
                "FPI Make CFP %": st.column_config.NumberColumn("FPI Make CFP %", format="%.1f%%"),
                "FPI Title %": st.column_config.NumberColumn("FPI Title %", format="%.1f%%"),
            })
        st.caption("**My** columns = 4,000-run Monte-Carlo of this exact bracket off my blended rating. "
                   "**FPI** columns = ESPN's independent full-season simulation. Both update live each week.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: 2026 RANKINGS
# ══════════════════════════════════════════════════════════════════════════════
if page == "Preseason Rankings":
    if not has_v2:
        st.warning("V2 model data not found. Run `python model_v2.py` to generate rankings.")
    else:
        f1,f2,f3,f4,f5=st.columns([2,2,2,2,1])
        with f1:
            conf_opts=["All"]+sorted(v2["conference"].dropna().unique().tolist()) if "conference" in v2.columns else ["All"]
            cf=st.selectbox("Conference",conf_opts,key="cf")
        with f2: mf=st.selectbox("Movement vs 2025",["All","Risers (↑5+)","Fallers (↓5+)","Stable"],key="mf")
        with f3: qf=st.selectbox("QB Status",["All","Returning","Transfer","Battle/Unknown"],key="qf")
        with f4: search=st.text_input("Search team","",key="rsearch")
        with f5: top_n=st.selectbox("Show",[10,15,25,50,len(v2)],index=2,key="rn")

        disp=v2.copy()
        if cf!="All" and "conference" in v2.columns: disp=disp[disp["conference"]==cf]
        if mf=="Risers (↑5+)": disp=disp[disp["delta_vs_2025"]>=5]
        elif mf=="Fallers (↓5+)": disp=disp[disp["delta_vs_2025"]<=-5]
        elif mf=="Stable": disp=disp[disp["delta_vs_2025"].abs()<5]
        if qf=="Returning": disp=disp[disp["qb_type"]=="returning"]
        elif qf=="Transfer": disp=disp[disp["qb_type"]=="transfer"]
        elif qf=="Battle/Unknown": disp=disp[~disp["qb_type"].isin(["returning","transfer"])]
        if search: disp=disp[disp["School"].str.contains(search,case=False,na=False)]
        disp=disp.sort_values("rank_v2").head(top_n)

        st.markdown("#### Top 10 — 2026 Preseason")
        top10=v2.sort_values("rank_v2").head(10)
        for chunk in [top10.iloc[:5],top10.iloc[5:]]:
            cols=st.columns(5)
            for i,(_,r) in enumerate(chunk.iterrows()):
                d=int(r.get("delta_vs_2025",0))
                dc="#7fd48b" if d>0 else ("#ef7d7d" if d<0 else "#5a5e7a")
                ds=f"+{d} vs 2025" if d>0 else(f"−{abs(d)} vs 2025" if d<0 else "— steady")
                qn=str(r.get("qb_name","?")); qs=qn[:16]+"…" if len(qn)>17 else qn
                conf=str(r.get("conference","")) if pd.notna(r.get("conference")) else ""
                rec=REC_2025.get(r["School"],"")
                cols[i].markdown(f"""<div class="top10-card" style="--tc:{team_color(r['School'])}">
                  <div class="rnk">#{int(r['rank_v2'])}</div>
                  <div class="team">{esc(r['School'])}</div>
                  <div class="idx">{r['power_index_v2']:.1f}</div>
                  <div class="delta" style="color:{dc}">{ds}</div>
                  <div class="qb">QB · {esc(qs)}</div>
                  <div class="conf">{esc(conf)}{(' · '+rec+' in ’25') if rec else ''}</div>
                </div>""",unsafe_allow_html=True)

        st.write("")
        bar_colors=[team_color(s) for s in disp["School"]]
        fig=go.Figure()
        fig.add_trace(go.Bar(y=disp["School"],x=disp["power_index_v2"],orientation="h",
            marker=dict(color=bar_colors,line=dict(color="rgba(255,255,255,.25)",width=.5)),
            text=[f"{v:.1f}" for v in disp["power_index_v2"]],
            textposition="outside",textfont=dict(size=11,color="#9a9eb8"),
            customdata=np.stack([disp["Rank_2025"],disp["delta_vs_2025"],disp["qb_name"],disp["qb_type"]],axis=-1),
            hovertemplate="<b>%{y}</b><br>PI: %{x:.1f}<br>2025 Rank: #%{customdata[0]}<br>Δ: %{customdata[1]:+.0f}<br>QB: %{customdata[2]} (%{customdata[3]})<extra></extra>"))
        fig.update_layout(**PL,title=f"2026 Power Index — top {len(disp)} (bars in team colors)",
            height=max(420,len(disp)*30),yaxis=dict(autorange="reversed"),
            xaxis_title="Power Index (0-100)",showlegend=False,
            margin=dict(l=150,r=70,t=45,b=20))
        sf(fig); st.plotly_chart(fig,use_container_width=True)

        # Why explainer with component bars
        st.markdown("#### Why does a team rank here?")
        cwhy1,cwhy2=st.columns([1,2])
        with cwhy1:
            et=st.selectbox("Select team",teams_sorted,key="et")
        er=v2[v2["School"]==et].iloc[0]
        comp_vals=[(lbl,gc(er,col),wt) for col,lbl,wt in COMPONENTS if col in v2.columns]
        with cwhy2:
            fc=go.Figure()
            cv=sorted(comp_vals,key=lambda x:x[1])
            fc.add_trace(go.Bar(y=[f"{l}  ({w}%)" for l,_,w in cv],x=[v for _,v,_ in cv],
                orientation="h",marker=dict(color=[GREEN if v>=65 else(RED if v<48 else GOLD) for _,v,_ in cv]),
                text=[f"{v:.0f}" for _,v,_ in cv],textposition="outside",textfont=dict(size=10)))
            fc.update_layout(**PL,title_text="",height=300,xaxis=dict(range=[0,110]),showlegend=False,
                             margin=dict(l=10,r=30,t=10,b=10))
            sf(fc); st.plotly_chart(fc,use_container_width=True)
        s2=sorted(comp_vals,key=lambda x:-x[1])
        t3=[x for x in s2 if x[1]>=65][:3]; w2=[x for x in s2 if x[1]<52][:2]
        msg=f"**{et}** ranks **#{int(er['rank_v2'])}** (2025: #{int(er['Rank_2025'])}, Δ{int(er['delta_vs_2025']):+d}). "
        if t3: msg+="Carrying it: "+", ".join(f"**{n}** ({v:.0f})" for n,v,_ in t3)+". "
        if w2: msg+="Dragging it: "+", ".join(f"{n} ({v:.0f})" for n,v,_ in w2)+". "
        qn=str(er.get("qb_name","TBD"))
        if er.get("qb_type")=="returning": msg+=f"QB **{qn}** returns."
        elif er.get("qb_type")=="transfer": msg+=f"Transfer QB **{qn}** arrives."
        else: msg+="⚠️ QB situation unresolved — model uncertainty elevated."
        st.markdown(f'<div class="note">{md_b(msg)}</div>',unsafe_allow_html=True)

        st.markdown("#### Full Rankings — every component")
        show=["rank_v2","School","conference","power_index_v2","Rank_2025","delta_vs_2025","qb_name"]+[c for c,_,_ in COMPONENTS]
        show=[c for c in show if c in disp.columns]
        tbl=disp[show].copy()
        ren={"rank_v2":"Rk","School":"Team","conference":"Conf","power_index_v2":"PI",
             "Rank_2025":"’25","delta_vs_2025":"Δ","qb_name":"QB"}
        ren.update({c:l for c,l,_ in COMPONENTS})
        tbl=tbl.rename(columns=ren)
        num_cols=[l for _,l,_ in COMPONENTS if l in tbl.columns]
        sty=tbl.style.format({"PI":"{:.1f}","’25":"{:.0f}","Δ":"{:+.0f}",**{c:"{:.0f}" for c in num_cols}})
        st.dataframe(sty,use_container_width=True,hide_index=True,height=min(900,len(tbl)*38+40))

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: TEAM HQ
# ══════════════════════════════════════════════════════════════════════════════
if page == "Team HQ":
    team=st.selectbox("Select team",teams_sorted,key="ti")
    r2=v2[v2["School"]==team].iloc[0] if has_v2 else None
    _r1match=v1[v1["School"]==to_v1_name(team)] if has_v1 else pd.DataFrame()
    r1=_r1match.iloc[0] if not _r1match.empty else None
    c1c=team_color(team)
    conf=str(r2.get("conference","")) if r2 is not None and pd.notna(r2.get("conference")) else ""
    rec=REC_2025.get(team,"—")
    st.markdown(f"""<div class="tbanner" style="--c1:{c1c}">
      <div class="tname">{esc(team)}</div>
      <div class="tmeta">{esc(conf)} &nbsp;·&nbsp; 2025 record: {rec} &nbsp;·&nbsp; QB: {esc(str(r2.get('qb_name','TBD')) if r2 is not None else 'TBD')}</div>
      <div class="bigrank">#{int(r2['rank_v2']) if r2 is not None else '—'}</div>
    </div>""",unsafe_allow_html=True)

    k1,k2,k3,k4,k5=st.columns(5)
    if r2 is not None:
        d=int(r2["delta_vs_2025"])
        dc="#7fd48b" if d>0 else ("#ef7d7d" if d<0 else "#8a8ea8")
        ds="Riser" if d>0 else("Faller" if d<0 else "Stable")
        k1.markdown(f'<div class="kpi"><div class="lbl">2026 Rank</div><div class="val">#{int(r2["rank_v2"])}</div><div class="sub">of {len(v2)} FBS</div></div>',unsafe_allow_html=True)
        k2.markdown(f'<div class="kpi"><div class="lbl">Power Index</div><div class="val">{r2["power_index_v2"]:.1f}</div><div class="sub">strength {r2.get("team_strength_rating",r2["power_index_v2"]):.1f}</div></div>',unsafe_allow_html=True)
        k3.markdown(f'<div class="kpi"><div class="lbl">2025 Rank</div><div class="val">#{int(r2["Rank_2025"])}</div><div class="sub">{rec} record</div></div>',unsafe_allow_html=True)
        k4.markdown(f'<div class="kpi"><div class="lbl">Movement</div><div class="val" style="color:{dc}">{d:+d}</div><div class="sub">{ds}</div></div>',unsafe_allow_html=True)
        pn=gc(r2,"portal_net_value",0)
        pc="#7fd48b" if pn>0 else ("#ef7d7d" if pn<0 else "#8a8ea8")
        k5.markdown(f'<div class="kpi"><div class="lbl">Portal Net Value</div><div class="val" style="color:{pc}">{pn:+.0f}</div><div class="sub">{int(gc(r2,"transfer_count",0))} arrivals</div></div>',unsafe_allow_html=True)

    # Depth chart field
    st.markdown("#### Projected 2026 Depth Chart")
    st.caption("Reconciled to the **live 2026 roster** — 2025 producers who actually returned, "
               "portal arrivals that landed (blue accent), and current-roster players with no 2025 "
               "stats filling out the two-deep. ★ = top-5 nationally at the position in 2025.")
    picks,ins,outs,tdep=pick_depth(team)
    st.markdown(field_html(team,picks,AA_KEYS),unsafe_allow_html=True)

    # Roster ledger — portal ins, plus ALL exits (portal + draft/graduation)
    st.markdown("#### Roster Ledger — every arrival and departure")
    cin,cout=st.columns(2)
    with cin:
        st.markdown(f'<span class="chip g">ARRIVALS · {len(ins)}</span>',unsafe_allow_html=True)
        if not ins.empty:
            it=ins[["player","position","origin","rating","stars"]].copy().sort_values("rating",ascending=False,na_position="last")
            it.columns=["Player","Pos","From","Rating","Stars"]
            st.dataframe(it.style.format({"Rating":"{:.2f}","Stars":"{:.0f}"},na_rep="—"),
                         use_container_width=True,hide_index=True,height=min(420,len(it)*36+40))
        else: st.caption("No portal arrivals this cycle.")
    with cout:
        n_dep=len(outs)+len(tdep)
        st.markdown(f'<span class="chip r">DEPARTURES · {n_dep}</span>',unsafe_allow_html=True)
        dep_rows=[]
        if not outs.empty:
            for _,o in outs.iterrows():
                reason=(f"Portal → {o['destination']}" if pd.notna(o["destination"])
                        else "Transferred out")
                dep_rows.append({"Player":o["player"],"Pos":o["position"],
                                 "Reason":reason,
                                 "Rating":o["rating"] if pd.notna(o["rating"]) else np.nan})
        if not tdep.empty:
            w_all_=pstats_wide()
            for _,o in tdep.iterrows():
                hit=w_all_[(w_all_["_nm"]==o["_nm"])&(w_all_["team"]==team)] if not w_all_.empty else pd.DataFrame()
                pos=hit.iloc[0]["position"] if len(hit) else "—"
                dep_rows.append({"Player":o["player"],"Pos":pos,"Reason":o["reason"],"Rating":np.nan})
        if dep_rows:
            dt=pd.DataFrame(dep_rows)
            dt["Rating"]=pd.to_numeric(dt["Rating"],errors="coerce")
            dt=dt.sort_values(["Reason","Rating"],ascending=[True,False],na_position="last")
            st.dataframe(dt.style.format({"Rating":"{:.2f}"},na_rep="—"),
                         use_container_width=True,hide_index=True,height=min(420,len(dt)*36+40))
        else: st.caption("No departures this cycle.")

    # Radar + efficiency
    cr,cb=st.columns(2)
    if r2 is not None:
        cats=[l for c,l,_ in COMPONENTS if c in v2.columns]
        vals=[gc(r2,c) for c,l,_ in COMPONENTS if c in v2.columns]
        with cr:
            st.markdown("#### 2026 Component Radar")
            cc=cats+[cats[0]]; vc=vals+[vals[0]]
            fr=go.Figure()
            fr.add_trace(go.Scatterpolar(r=vc,theta=cc,fill="toself",name="2026",
                line_color=txt_color(team),fillcolor="rgba(200,170,110,.15)"))
            fr.update_layout(**PL,title_text="",height=380,showlegend=False,
                polar=dict(bgcolor="rgba(0,0,0,0)",
                    radialaxis=dict(visible=True,range=[0,100],gridcolor="#161a2e",tickfont=dict(size=8,color="#4a4e6a")),
                    angularaxis=dict(gridcolor="#1e2240",tickfont=dict(size=9,color="#b0b4c8"))))
            st.plotly_chart(fr,use_container_width=True)
    if r1 is not None:
        with cb:
            st.markdown("#### 2025 Efficiency Profile (z-scores)")
            eff_labels=["Off Eff","Explosive","Def Eff","Havoc","Net PPG","Net Yds"]
            all_v1=v1[["Off_Efficiency","Explosive_Score","Def_Efficiency","Def_Havoc_Rate","Net_PPG","Net_Yds"]].copy()
            zz=zscore(all_v1)
            row_z=zz[v1.index.get_loc(r1.name)]
            bc2=[GREEN if z>0 else RED for z in row_z]; bc2[2]=GREEN if row_z[2]<0 else RED
            fb=go.Figure(go.Bar(x=eff_labels,y=row_z,marker_color=bc2,
                text=[f"{z:+.2f}" for z in row_z],textposition="outside",
                textfont=dict(size=11,color="#9a9eb8")))
            fb.update_layout(**PL,title_text="",height=380,yaxis_title="Z vs FBS Avg",showlegend=False,
                margin=dict(l=20,r=20,t=40,b=40))
            sf(fb); st.plotly_chart(fb,use_container_width=True)

    # Scouting report
    if r2 is not None:
        comp_vals=[(l,gc(r2,c)) for c,l,_ in COMPONENTS if c in v2.columns]
        s3=sorted(comp_vals,key=lambda x:-x[1])
        t3s=[x for x in s3 if x[1]>=65][:3]; w2s=[x for x in s3 if x[1]<52][:2]
        rpt=f"**{team}** projects **#{int(r2['rank_v2'])}** entering 2026 (Δ{int(r2['delta_vs_2025']):+d} vs 2025). "
        if t3s: rpt+="Strengths: "+", ".join(f"**{n}** ({v:.0f})" for n,v in t3s)+". "
        if w2s: rpt+="Concerns: "+", ".join(f"{n} ({v:.0f})" for n,v in w2s)+". "
        if not ins.empty and ins["rating"].notna().any():
            best=ins.sort_values("rating",ascending=False).iloc[0]
            rpt+=f"Headline add: **{best['player']}** ({best['position']}, {best['origin']}). "
        if not outs.empty and outs["rating"].notna().any():
            worst=outs.sort_values("rating",ascending=False).iloc[0]
            rpt+=f"Biggest loss: {worst['player']} ({worst['position']} → {worst['destination'] if pd.notna(worst['destination']) else 'portal'})."
        st.markdown(f'<div class="note">{md_b(rpt)}</div>',unsafe_allow_html=True)

    # Schedule
    tg=team_games(team)
    if not tg.empty:
        w=int((tg["Pick"]=="W").sum()); l=int((tg["Pick"]=="L").sum())
        ranked=tg["Opp Rank"].dropna()
        home_ct=int((tg["Site"]=="Home").sum())
        st.markdown("#### 2026 Schedule — game by game")
        sk1,sk2,sk3,sk4=st.columns(4)
        sk1.markdown(f'<div class="kpi"><div class="lbl">Projected Record</div><div class="val">{w}–{l}</div><div class="sub">{len(tg)} games</div></div>',unsafe_allow_html=True)
        sk2.markdown(f'<div class="kpi"><div class="lbl">Home Games</div><div class="val">{home_ct}</div><div class="sub">gold rows below</div></div>',unsafe_allow_html=True)
        sk3.markdown(f'<div class="kpi"><div class="lbl">Avg Opp Rank</div><div class="val">{ranked.mean():.0f}</div><div class="sub">rated opponents</div></div>' if len(ranked) else '<div class="kpi"><div class="lbl">Avg Opp Rank</div><div class="val">—</div></div>',unsafe_allow_html=True)
        sk4.markdown(f'<div class="kpi"><div class="lbl">Top-25 Foes</div><div class="val">{int((ranked<=25).sum()) if len(ranked) else 0}</div><div class="sub">ranked matchups</div></div>',unsafe_allow_html=True)
        st.write("")
        for _,g in tg.iterrows():
            is_home=g["Site"]=="Home"
            wk=int(g["Wk"]) if pd.notna(g["Wk"]) else "—"
            oppr=f"#{int(g['Opp Rank'])}" if pd.notna(g["Opp Rank"]) else "NR"
            pcls="pick-w" if g["Pick"]=="W" else "pick-l"
            site_icon="HOME" if is_home else ("AWAY" if g["Site"]=="Away" else "NEUTRAL")
            ven=str(g.get("Venue","") or "")
            st.markdown(f"""<div class="schrow {'home' if is_home else ''}">
              <span class="wk">WK {wk}</span>
              <span class="opp">{esc(g['Opponent'])} <span style="color:#8489b4;font-size:.72rem">{oppr}</span></span>
              <span class="ven">{esc(ven)}</span>
              <span style="color:#8489b4;font-size:.72rem;font-weight:700">{site_icon}</span>
              <span style="color:#b0b4c8">{int(g['Win %'])}%</span>
              <span class="{pcls}">{g['Pick']}</span>
            </div>""",unsafe_allow_html=True)
        st.caption("Win % = strength rating + home field through the logistic model. Unrated/FCS opponents shown as heavy favorites.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4: GAME PREDICTOR
# ══════════════════════════════════════════════════════════════════════════════
if page == "Game Predictor":
    st.markdown("### Game Predictor")
    mode=st.radio("Model basis",["2026 V2 (preseason)","2025 V1 (historical)"],horizontal=True,key="pred_mode")
    use_v2_pred=(mode=="2026 V2 (preseason)") and has_v2
    use_v1_pred=(mode=="2025 V1 (historical)") and has_v1
    pred_teams=v2.sort_values("rank_v2")["School"].tolist() if use_v2_pred else (v1.sort_values("Power_Rank")["School"].tolist() if use_v1_pred else teams_sorted)

    c1,c2,c3=st.columns([2,1,2])
    with c1: ta=st.selectbox("Team A",pred_teams,index=0,key="gpa")
    with c2: venue=st.radio("Venue",["Neutral","A home","B home"],key="gpv")
    with c3: tb=st.selectbox("Team B",pred_teams,index=2,key="gpb")

    w1,w2,w3=st.columns(3)
    with w1: wind=st.slider("Wind (mph)",0,40,0,key="wind")
    with w2: precip=st.checkbox("Precipitation",key="precip")
    with w3: cold=st.checkbox("Cold (<35°F)",key="cold")

    def qb_row(t):
        if qbs_df.empty: return None
        m=qbs_df[qbs_df["team"]==t]
        return m.iloc[0] if not m.empty else None

    if use_v2_pred:
        ra=v2[v2["School"]==ta].iloc[0]; rb=v2[v2["School"]==tb].iloc[0]
        pa=ra[STRENGTH_COL]; pb=rb[STRENGTH_COL]
        qa=gc(ra,"qb_score"); qbsc=gc(rb,"qb_score")
        pa_adj=pa+(qa-65)*0.06; pb_adj=pb+(qbsc-65)*0.06
        hfa=0.0
        big_home={"Michigan","Penn State","Ohio State","Tennessee","Texas A&M","Alabama","LSU","Texas","Georgia","Oregon","Notre Dame"}
        if venue=="A home": hfa=4.0 if ta in big_home else 2.7
        elif venue=="B home": hfa=-(4.0 if tb in big_home else 2.7)
        wx=0.0
        if wind>=20: wx+=(wind-15)*0.12
        if precip: wx+=1.2
        if cold: wx+=0.8
        qra,qrb=qb_row(ta),qb_row(tb)
        ya=qra["ypa_2025"] if qra is not None and pd.notna(qra.get("ypa_2025")) else 7.5
        yb=qrb["ypa_2025"] if qrb is not None and pd.notna(qrb.get("ypa_2025")) else 7.5
        if ya>yb: pa_adj-=wx
        else: pb_adj-=wx
        k=0.1; prob_a=1/(1+np.exp(-k*((pa_adj-pb_adj)+hfa)))
        margin=(pa_adj-pb_adj+hfa)*0.38
        qb_a_name=str(ra.get("qb_name","?")); qb_b_name=str(rb.get("qb_name","?"))
    elif use_v1_pred:
        ra=v1[v1["School"]==ta].iloc[0]; rb=v1[v1["School"]==tb].iloc[0]
        pa=ra["Power_Index"]; pb=rb["Power_Index"]
        hfa=0.4 if venue=="A home" else (-0.4 if venue=="B home" else 0)
        k=1.2; prob_a=1/(1+np.exp(-k*((pa-pb)+hfa)))
        margin=(pa-pb+hfa)*15
        pa_adj=pa; pb_adj=pb; qa=qbsc=50
        qb_a_name="—"; qb_b_name="—"
    else:
        st.error("No model data available."); st.stop()

    fav=ta if prob_a>0.5 else tb
    proj_a=max(10,round(23+margin/2)); proj_b=max(7,round(23-margin/2))
    ca,cbb=team_color(ta),team_color(tb)
    ca_t,cbb_t=txt_color(ta),txt_color(tb)

    m1,m2,m3=st.columns([2,3,2])
    m1.markdown(f'''<div class="kpi" style="border-top:3px solid {ca}"><div class="lbl">{esc(ta)}</div>
        <div class="val" style="color:{ca_t}">{prob_a*100:.0f}%</div>
        <div class="sub">QB · {esc(qb_a_name)}</div></div>''',unsafe_allow_html=True)
    m2.markdown(f'''<div class="kpi"><div class="lbl">Projected Score</div>
        <div class="val">{proj_a} – {proj_b}</div>
        <div class="sub">{esc(fav)} by ~{abs(margin):.1f} · O/U ≈ {proj_a+proj_b}</div></div>''',unsafe_allow_html=True)
    m3.markdown(f'''<div class="kpi" style="border-top:3px solid {cbb}"><div class="lbl">{esc(tb)}</div>
        <div class="val" style="color:{cbb_t}">{(1-prob_a)*100:.0f}%</div>
        <div class="sub">QB · {esc(qb_b_name)}</div></div>''',unsafe_allow_html=True)

    st.markdown(f"""<div style="margin:14px 0 4px;height:26px;border-radius:999px;overflow:hidden;display:flex;border:1px solid #202750">
      <div style="width:{prob_a*100:.1f}%;background:linear-gradient(90deg,{ca}cc,{ca});display:flex;align-items:center;justify-content:flex-start;padding-left:12px;font-size:.72rem;font-weight:800;color:#fff">{esc(ta)} {prob_a*100:.0f}%</div>
      <div style="flex:1;background:linear-gradient(90deg,{cbb},{cbb}cc);display:flex;align-items:center;justify-content:flex-end;padding-right:12px;font-size:.72rem;font-weight:800;color:#fff">{(1-prob_a)*100:.0f}% {esc(tb)}</div>
    </div>""",unsafe_allow_html=True)

    if use_v2_pred:
        h2h1,h2h2=st.columns(2)
        with h2h1:
            st.markdown("#### Tale of the Tape — model components")
            cats=[l for c,l,_ in COMPONENTS if c in v2.columns and c not in("schedule_strength_score","conference_strength_score")]
            va=[gc(ra,c) for c,l,_ in COMPONENTS if c in v2.columns and c not in("schedule_strength_score","conference_strength_score")]
            vb=[gc(rb,c) for c,l,_ in COMPONENTS if c in v2.columns and c not in("schedule_strength_score","conference_strength_score")]
            ft=go.Figure()
            ft.add_trace(go.Bar(y=cats,x=[-v for v in va],orientation="h",name=ta,
                marker_color=ca_t,text=[f"{v:.0f}" for v in va],textposition="outside",textfont=dict(size=10)))
            ft.add_trace(go.Bar(y=cats,x=vb,orientation="h",name=tb,
                marker_color=cbb_t,text=[f"{v:.0f}" for v in vb],textposition="outside",textfont=dict(size=10)))
            ft.update_layout(**PL,title_text="",barmode="overlay",height=340,
                xaxis=dict(range=[-115,115],tickvals=[-100,-50,0,50,100],ticktext=["100","50","0","50","100"]),
                legend=dict(orientation="h",x=.5,xanchor="center",y=1.12),
                margin=dict(l=10,r=10,t=30,b=10))
            sf(ft); st.plotly_chart(ft,use_container_width=True)
        with h2h2:
            st.markdown("#### 2025 Advanced Efficiency — offense vs defense")
            if not adv_df.empty:
                aa_=adv_df[adv_df["team"]==ta]; ab_=adv_df[adv_df["team"]==tb]
                if not aa_.empty and not ab_.empty:
                    aa_=aa_.iloc[0]; ab_=ab_.iloc[0]
                    metrics=[("Off PPA","offense.ppa",True),("Off Success %","offense.successRate",True),
                             ("Off Explosiveness","offense.explosiveness",True),("Def PPA","defense.ppa",False),
                             ("Def Success %","defense.successRate",False),("Havoc","defense.havoc.total",True)]
                    rows=[]
                    for lbl,col,hib in metrics:
                        if col in adv_df.columns:
                            va_=float(aa_[col]); vb_=float(ab_[col])
                            better_a=(va_>vb_)==hib
                            rows.append((lbl,va_,vb_,better_a))
                    tt=""
                    for lbl,va_,vb_,ba in rows:
                        wa="700" if ba else "400"; wb="400" if ba else "700"
                        ca_c=ca_t if ba else "#8489b4"; cb_c="#8489b4" if ba else cbb_t
                        tt+=(f'<div style="display:grid;grid-template-columns:1fr 130px 1fr;padding:7px 10px;'
                             f'border-bottom:1px solid #1a2038;font-size:.82rem">'
                             f'<span style="text-align:right;color:{ca_c};font-weight:{wa}">{va_:.3f}</span>'
                             f'<span style="text-align:center;color:#8a8ea8;font-size:.7rem;text-transform:uppercase;letter-spacing:.5px">{lbl}</span>'
                             f'<span style="color:{cb_c};font-weight:{wb}">{vb_:.3f}</span></div>')
                    st.markdown(f'<div class="card" style="padding:8px 6px">{tt}</div>',unsafe_allow_html=True)
                    st.caption("Bold = advantage. PPA = predicted points added per play (EPA).")
                else:
                    st.info("Advanced 2025 stats unavailable for one of these teams.")

        # QB duel card
        qra,qrb=qb_row(ta),qb_row(tb)
        if qra is not None or qrb is not None:
            st.markdown("#### QB Duel")
            qc1,qc2=st.columns(2)
            for col,qq,tt,cc in [(qc1,qra,ta,ca),(qc2,qrb,tb,cbb)]:
                with col:
                    if qq is None:
                        st.info(f"No QB data for {tt}."); continue
                    yds=f"{int(qq['yds_2025']):,}" if pd.notna(qq.get("yds_2025")) else "—"
                    tds=int(qq["td_2025"]) if pd.notna(qq.get("td_2025")) else "—"
                    ints=int(qq["int_2025"]) if pd.notna(qq.get("int_2025")) else "—"
                    pct=f"{qq['pct_2025']*100:.0f}%" if pd.notna(qq.get("pct_2025")) and qq["pct_2025"]<=1 else (f"{qq['pct_2025']:.0f}%" if pd.notna(qq.get("pct_2025")) else "—")
                    ypa=f"{qq['ypa_2025']:.1f}" if pd.notna(qq.get("ypa_2025")) else "—"
                    st.markdown(f"""<div class="card" style="border-top:3px solid {cc}">
                      <div style="font-size:1rem;font-weight:800;color:#f2efe6">{esc(str(qq['qb']))}
                        <span style="font-size:.7rem;color:#8489b4;font-weight:600">· {esc(str(qq.get('status','')))}</span></div>
                      <div style="display:flex;gap:20px;margin-top:8px;flex-wrap:wrap;font-size:.8rem">
                        <span>YDS <b style="color:#c8aa6e">{yds}</b></span>
                        <span>TD <b style="color:#7fd48b">{tds}</b></span>
                        <span>INT <b style="color:#ef7d7d">{ints}</b></span>
                        <span>CMP <b>{pct}</b></span>
                        <span>YPA <b>{ypa}</b></span>
                      </div></div>""",unsafe_allow_html=True)

        # QB swap what-if
        st.markdown("#### What-if: swap in any projected 2026 starter")
        if not qbs_df.empty and has_v2:
            qsc=dict(zip(v2["School"],v2["qb_score"])) if "qb_score" in v2.columns else {}
            opts=[f"{r['qb']} — {r['team']}" for _,r in qbs_df.sort_values("team").iterrows()]
            qa2,qb2=st.columns(2)
            with qa2: sela=st.selectbox(f"QB for {ta}",["Use current"]+opts,key="ha")
            with qb2: selb=st.selectbox(f"QB for {tb}",["Use current"]+opts,key="hb")
            def swap_score(sel,default):
                if sel=="Use current": return default
                t=sel.split(" — ")[-1]
                return qsc.get(t,default)
            hsa=swap_score(sela,qa); hsb=swap_score(selb,qbsc)
            if sela!="Use current" or selb!="Use current":
                pah=pa+(hsa-65)*0.06; pbh=pb+(hsb-65)*0.06
                probh=1/(1+np.exp(-k*((pah-pbh)+hfa)))
                diff=(probh-prob_a)*100
                st.markdown(f'<div class="note"><strong>Hypothetical:</strong> with those QBs, {ta} win probability → <b>{probh*100:.1f}%</b> (base {prob_a*100:.1f}%) — a <b>{diff:+.1f}pp</b> swing.</div>',unsafe_allow_html=True)

    # League-wide projected records
    if has_v2:
        st.markdown("---")
        st.markdown("### Projected 2026 Records — Whole League")
        recs=projected_records()
        if recs.empty:
            st.info("No 2026 schedule loaded.")
        else:
            recs=recs.merge(v2[["School","rank_v2"]+(["conference"] if "conference" in v2.columns else [])],on="School",how="left")
            recs["Record"]=recs["Proj W"].astype(int).astype(str)+"–"+recs["Proj L"].astype(int).astype(str)
            fpr=st.columns([2,1])
            with fpr[0]:
                conf_o=["All"]+sorted(recs["conference"].dropna().unique().tolist()) if "conference" in recs.columns else ["All"]
                pc=st.selectbox("Conference",conf_o,key="prc")
            rv=recs if pc=="All" else recs[recs["conference"]==pc]
            rv=rv.sort_values(["Proj W","rank_v2"],ascending=[False,True])
            cols=["rank_v2","School"]+(["conference"] if "conference" in rv.columns else [])+["Record","Proj W","Proj L","Games"]
            tblp=rv[cols].rename(columns={"rank_v2":"Rank","conference":"Conf"})
            st.dataframe(tblp,use_container_width=True,hide_index=True,height=520)
            st.caption("Every team's real 2026 slate through the strength-based win model (home/away/neutral aware).")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5: PORTAL LAB — full CFBD portal with openable player cards
# ══════════════════════════════════════════════════════════════════════════════
if page == "Portal Lab":
    st.markdown("### Transfer Portal Lab — 2026")
    if portal_df.empty:
        st.warning("No portal file found (data/raw/2026_transfer_portal_cfbd.csv).")
    else:
        landed=portal_df["destination"].notna().sum()
        pk1,pk2,pk3,pk4=st.columns(4)
        pk1.markdown(f'<div class="kpi"><div class="lbl">Players in Portal</div><div class="val">{len(portal_df):,}</div><div class="sub">2026 cycle</div></div>',unsafe_allow_html=True)
        pk2.markdown(f'<div class="kpi"><div class="lbl">Committed</div><div class="val">{landed:,}</div><div class="sub">{landed/len(portal_df)*100:.0f}% found homes</div></div>',unsafe_allow_html=True)
        top_dest=portal_df["destination"].mode()
        pk3.markdown(f'<div class="kpi"><div class="lbl">Busiest Destination</div><div class="val" style="font-size:1.25rem">{esc(top_dest.iloc[0]) if len(top_dest) else "—"}</div><div class="sub">{int((portal_df["destination"]==top_dest.iloc[0]).sum()) if len(top_dest) else 0} adds</div></div>',unsafe_allow_html=True)
        elite_ct=int((portal_df["rating"]>=0.93).sum())
        pk4.markdown(f'<div class="kpi"><div class="lbl">Elite Movers</div><div class="val">{elite_ct}</div><div class="sub">rating ≥ 0.93</div></div>',unsafe_allow_html=True)

        # Net portal value leaderboard
        if has_v2 and "portal_net_value" in v2.columns:
            st.markdown("#### Portal Winners & Losers — net roster value moved")
            pn=v2[["School","portal_net_value"]].dropna().sort_values("portal_net_value")
            big=pd.concat([pn.head(10),pn.tail(10)])
            fpn=go.Figure(go.Bar(y=big["School"],x=big["portal_net_value"],orientation="h",
                marker_color=[GREEN if x>0 else RED for x in big["portal_net_value"]],
                text=[f"{x:+.0f}" for x in big["portal_net_value"]],textposition="outside",textfont=dict(size=10)))
            fpn.update_layout(**PL,title_text="",height=480,showlegend=False,margin=dict(l=130,r=60,t=20,b=20),
                              xaxis_title="Net portal value (arrivals − departures, position-weighted)")
            sf(fpn); st.plotly_chart(fpn,use_container_width=True)

        st.markdown("#### Every Portal Move — open any player card")
        ff1,ff2,ff3,ff4,ff5=st.columns([2,2,2,2,1])
        with ff1: pos_f=st.multiselect("Position",sorted(portal_df["position"].dropna().unique().tolist()),key="ppos")
        with ff2: team_f=st.text_input("Team (from or to)","",key="pteam")
        with ff3: name_f=st.text_input("Player name","",key="pname")
        with ff4: min_stars=st.selectbox("Min stars",["Any",4,3,2],key="pstars")
        with ff5: sort_by=st.selectbox("Sort",["Rating","Stars","Name"],key="psort")

        filt=portal_df.copy()
        if pos_f: filt=filt[filt["position"].isin(pos_f)]
        if team_f:
            tl=team_f.lower()
            filt=filt[filt["origin"].astype(str).str.lower().str.contains(tl,na=False)|
                      filt["destination"].astype(str).str.lower().str.contains(tl,na=False)]
        if name_f: filt=filt[filt["player"].str.lower().str.contains(name_f.lower(),na=False)]
        if min_stars!="Any": filt=filt[filt["stars"]>=int(min_stars)]
        if sort_by=="Rating": filt=filt.sort_values("rating",ascending=False,na_position="last")
        elif sort_by=="Stars": filt=filt.sort_values(["stars","rating"],ascending=False,na_position="last")
        else: filt=filt.sort_values("player")

        per_page=25
        n_pages=max(1,int(np.ceil(len(filt)/per_page)))
        pg1,pg2=st.columns([1,4])
        with pg1: page=st.number_input(f"Page (of {n_pages})",1,n_pages,1,key="ppage")
        with pg2: st.caption(f"{len(filt):,} players match — showing {per_page}/page, sorted by {sort_by.lower()}. Click a row to open the full card.")
        sub=filt.iloc[(page-1)*per_page:page*per_page]

        w_all=pstats_wide()
        conf_of=dict(zip(v2["School"],v2["conference"])) if has_v2 and "conference" in v2.columns else {}
        P4={"SEC","Big Ten","Big 12","ACC"}

        def portal_story(r,srow):
            nm=r["player"]; pos=r["position"]; org=str(r.get("origin","?")); dst=r.get("destination")
            rating=r.get("rating"); stars=r.get("stars"); elig=str(r.get("eligibility",""))
            tier=("an <b>elite, program-changing</b>" if pd.notna(rating) and rating>=.95 else
                  "a <b>blue-chip</b>" if pd.notna(rating) and rating>=.90 else
                  "a <b>proven</b>" if pd.notna(rating) and rating>=.85 else
                  "a <b>depth/upside</b>")
            s=f"<b>{esc(nm)}</b> enters the 2026 cycle as {tier} {esc(pos)} out of <b>{esc(org)}</b>. "
            if pd.notna(dst):
                co,cd=conf_of.get(org),conf_of.get(dst)
                jump=""
                if co and cd and co!=cd:
                    if cd in P4 and co not in P4: jump=f" — a big step up from the {esc(co)} to the {esc(cd)}"
                    elif co in P4 and cd not in P4: jump=f" — dropping down from the {esc(co)} to the {esc(cd)}"
                    else: jump=f" — moving leagues, {esc(co)} → {esc(cd)}"
                s+=f"Committed to <b>{esc(str(dst))}</b>{jump}. "
            else:
                s+="<b>Still uncommitted</b> — one of the best available names left on the board. " if pd.notna(rating) and rating>=.9 else "Still in the portal, uncommitted. "
            if srow is not None:
                sl=stat_line(srow)
                if sl!="—": s+=f"2025 production at {esc(org)}: <b>{esc(sl)}</b>. "
            else:
                s+="No qualifying 2025 stat line (redshirt, injury, or depth role). "
            if (str(nm).lower(),org)in AA_KEYS or (srow is not None and (str(nm).lower(),srow.get('team'))in AA_KEYS):
                s+="★ <b>Model All-American in 2025</b> — top-5 nationally at the position. "
            nil=NIL_HEADLINERS.get((nm,dst if pd.notna(dst) else ""))
            if nil: s+=f"Reported NIL package: <b>{nil}</b>. "
            if elig and elig not in("nan","Immediate"): s+=f"Eligibility: {esc(elig)}."
            return s

        for _,r in sub.iterrows():
            stars_s="★"*int(r["stars"]) if pd.notna(r["stars"]) else "—"
            rt=f"{r['rating']:.2f}" if pd.notna(r["rating"]) else "—"
            dst=str(r["destination"]) if pd.notna(r["destination"]) else "Uncommitted"
            with st.expander(f"{stars_s}  {r['player']} · {r['position']} · {r['origin']} → {dst} · rating {rt}"):
                srow=None
                if not w_all.empty:
                    hit=w_all[(w_all["_nm"]==str(r["player"]).lower())&(w_all["team"]==r["origin"])]
                    if len(hit): srow=hit.iloc[0]
                cA,cB=st.columns([3,2])
                with cA:
                    st.markdown(f'<div style="font-size:.86rem;line-height:1.6">{portal_story(r,srow)}</div>',unsafe_allow_html=True)
                    if pd.notna(r["rating"]):
                        pctw=min(100,max(4,(r["rating"]-0.6)/0.4*100))
                        st.markdown(f'<div class="ratingbar"><div style="width:{pctw:.0f}%"></div></div>'
                                    f'<span style="font-size:.68rem;color:#8489b4">Portal rating {r["rating"]:.2f} · {stars_s}</span>',unsafe_allow_html=True)
                with cB:
                    if srow is not None:
                        stat_cols=[("passing_YDS","Pass Yds"),("passing_TD","Pass TD"),("passing_INT","INT"),
                                   ("rushing_YDS","Rush Yds"),("rushing_TD","Rush TD"),
                                   ("receiving_REC","Rec"),("receiving_YDS","Rec Yds"),("receiving_TD","Rec TD"),
                                   ("defensive_TOT","Tackles"),("defensive_TFL","TFL"),("defensive_SACKS","Sacks"),
                                   ("defensive_PD","PD"),("interceptions_INT","INT (def)")]
                        rows=[(lbl,int(srow[c])) for c,lbl in stat_cols
                              if c in srow.index and pd.notna(srow[c]) and float(srow[c])>0]
                        if rows:
                            st.markdown("**2025 Stats**")
                            st.dataframe(pd.DataFrame(rows,columns=["Stat","2025"]),hide_index=True,use_container_width=True)
                        else: st.caption("No 2025 counting stats recorded.")
                    else: st.caption("No 2025 stat line found at origin school.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 7: PLAYER STATS
# ══════════════════════════════════════════════════════════════════════════════
if page == "Player Stats":
    st.markdown("### Player Stat Leaderboards — 2025")
    ps=load_player_stats()
    if ps.empty:
        st.warning("No player-stats file found (data/raw/2025_player_stats.csv).")
    elif {"category","statType","stat"}.issubset(ps.columns):
        if "season" not in ps.columns: ps=ps.assign(season="2025")
        f1,f2,f3,f4=st.columns(4)
        cats=sorted(ps["category"].dropna().astype(str).str.lower().unique())
        dc="passing" if "passing" in cats else (cats[0] if cats else None)
        with f1: catsel=st.selectbox("Category",cats,index=cats.index(dc) if dc in cats else 0,key="pl_cat")
        confs=(["All"]+sorted(ps["conference"].dropna().astype(str).unique().tolist())) if "conference" in ps.columns else ["All"]
        with f2: cfsel=st.selectbox("Conference",confs,key="pl_conf")
        teams_p=sorted(ps["team"].dropna().unique().tolist()) if "team" in ps.columns else []
        with f3: tsel=st.selectbox("Team",["All"]+teams_p,key="pl_team")
        with f4: nshow=st.selectbox("Rows",[25,50,100,300],index=1,key="pl_n")

        sub=ps[ps["category"].astype(str).str.lower()==catsel].copy()
        if cfsel!="All" and "conference" in sub.columns: sub=sub[sub["conference"].astype(str)==cfsel]
        if tsel!="All" and "team" in sub.columns: sub=sub[sub["team"]==tsel]
        sub["stat"]=pd.to_numeric(sub["stat"],errors="coerce")
        idxc=[c for c in ["player","team","position"] if c in sub.columns]
        wide=sub.pivot_table(index=idxc,columns="statType",values="stat",aggfunc="first").reset_index()
        wide.columns.name=None
        sort_pref=["YDS","TOT","SACKS","PTS","REC","INT","TD","ATT"]
        scol=next((c for c in sort_pref if c in wide.columns),None)
        if scol: wide=wide.sort_values(scol,ascending=False,na_position="last")
        wide=wide.rename(columns={"player":"Player","team":"Team","position":"Pos"})
        st.caption(f"{len(wide):,} players — {catsel} (2025)" + ("" if cfsel=='All' else f" · {cfsel}"))
        disp=wide.head(nshow)
        disp=disp.astype(object).where(pd.notna(disp),"")
        st.dataframe(disp,use_container_width=True,hide_index=True,height=560)
    else:
        st.dataframe(ps.head(300),use_container_width=True,hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: 2025 CFP RETRO
# ══════════════════════════════════════════════════════════════════════════════
if page == "2025 CFP Retro":
    st.markdown("### 2025 CFP — Power Index Retrospective")
    if not has_v1:
        st.warning("Needs `cfb_combined_data.xlsx`. Place it in the app directory.")
    else:
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
        with col1:
            st.markdown("#### Power Index vs. Scoring Margin (2025)")
            cfp_df=v1[v1["Made_CFP"]==1]; non_cfp=v1[v1["Made_CFP"]==0]
            fig_s=go.Figure()
            fig_s.add_trace(go.Scatter(x=non_cfp["Power_Index"],y=non_cfp["Net_PPG"],
                mode="markers",marker=dict(color=GRAY,size=5,opacity=0.35),
                name="Other FBS",hovertemplate="%{text}<extra></extra>",text=non_cfp["School"]))
            fig_s.add_trace(go.Scatter(x=cfp_df["Power_Index"],y=cfp_df["Net_PPG"],
                mode="markers+text",text=cfp_df["School"],textposition="top right",
                textfont=dict(size=9,color=GOLD),
                marker=dict(color=GOLD,size=12,line=dict(width=1.5,color="#0a0d1a")),
                name="CFP Teams",hovertemplate="<b>%{text}</b><br>PI: %{x:.3f}<br>Net PPG: %{y:.1f}<extra></extra>"))
            fig_s.update_layout(**PL,title_text="",xaxis_title="Power Index",yaxis_title="Net PPG",height=400,
                legend=dict(x=0.02,y=0.98,bgcolor="rgba(0,0,0,0)"),margin=dict(l=20,r=20,t=25,b=20))
            fig_s.add_hline(y=0,line_dash="dash",line_color="#252850")
            fig_s.add_vline(x=0,line_dash="dash",line_color="#252850")
            sf(fig_s); st.plotly_chart(fig_s,use_container_width=True)
        with col2:
            st.markdown("#### CFP Seed vs. Power Index Rank")
            cfp_data=v1[v1["Made_CFP"]==1].copy()
            cfp_data["CFP_Seed"]=cfp_data["School"].map(CFP_SEEDS)
            cfp_data["Diff"]=cfp_data["CFP_Seed"]-cfp_data["Power_Rank"]
            cfp_data_sorted=cfp_data.sort_values("Power_Rank")
            dot_colors=[GREEN if d>=0 else RED for d in cfp_data_sorted["Diff"]]
            fig_sv=go.Figure()
            fig_sv.add_trace(go.Scatter(
                x=cfp_data_sorted["Power_Rank"],y=cfp_data_sorted["CFP_Seed"],
                mode="markers+text",text=cfp_data_sorted["School"],
                textposition="top right",textfont=dict(size=9,color="#b0b4c8"),
                marker=dict(color=dot_colors,size=12,line=dict(width=1.5,color="#0a0d1a")),
                hovertemplate="<b>%{text}</b><br>Power Rank: #%{x}<br>CFP Seed: #%{y}<extra></extra>"))
            fig_sv.add_trace(go.Scatter(x=[0,90],y=[0,13],mode="lines",
                line=dict(dash="dash",color="#252850"),showlegend=False))
            fig_sv.update_layout(**PL,title_text="",xaxis_title="Power Index Rank",yaxis_title="CFP Seed",
                yaxis=dict(autorange="reversed"),height=400,showlegend=False,margin=dict(l=20,r=20,t=25,b=20))
            sf(fig_sv); st.plotly_chart(fig_sv,use_container_width=True)

        st.markdown("#### Bracket Predictions — Retrodiction")
        rc={"First Round":BLUE,"Quarterfinal":GOLD,"Semifinal":RED,"Championship":GREEN}
        for rnd,a,b,actual,correct_g,conf in BRACKET:
            icon="✅" if correct_g else "❌"
            bg="rgba(110,200,122,.04)" if correct_g else "rgba(224,82,82,.06)"
            bc=f"rgba(110,200,122,.15)" if correct_g else "rgba(224,82,82,.2)"
            rcolor=rc.get(rnd,GOLD)
            st.markdown(f"""<div style="display:grid;grid-template-columns:110px 1fr 150px 110px 40px;
                gap:12px;align-items:center;background:{bg};border:1px solid {bc};
                border-left:3px solid {rcolor};border-radius:8px;padding:10px 14px;margin-bottom:6px">
                <span style="font-size:.72rem;color:{rcolor};font-weight:700;text-transform:uppercase">{rnd}</span>
                <span style="font-size:.88rem;color:#c8cbd8"><b style="color:#eae7e0">{a}</b> <span style="color:#3a3e5a">vs</span> <b style="color:#eae7e0">{b}</b></span>
                <span style="font-size:.78rem;color:#7a7ea8">Model: {a if conf>50 else b} ({conf}%)</span>
                <span style="font-size:.78rem;color:#eae7e0;font-weight:600">✓ {actual}</span>
                <span style="font-size:1.05rem;text-align:center">{icon}</span>
            </div>""",unsafe_allow_html=True)
        st.markdown('<div class="note"><strong>Both misses were coin-flips</strong> — Ohio State vs Miami (FL) at 55.6% and Ole Miss vs Miami (FL) at 55.7%. The model nailed every lopsided matchup and the champion.</div>',unsafe_allow_html=True)

        st.markdown("#### Power Index vs Committee — Full CFP Field")
        cfp_tbl=v1[v1["Made_CFP"]==1][["School","Power_Rank","Power_Index","Off_PPG","Def_PPG_Allowed","Net_PPG"]].copy()
        cfp_tbl["CFP_Seed"]=cfp_tbl["School"].map(CFP_SEEDS)
        cfp_tbl["Δ Seed−Rank"]=cfp_tbl["CFP_Seed"]-cfp_tbl["Power_Rank"]
        cfp_tbl=cfp_tbl.sort_values("CFP_Seed").reset_index(drop=True)
        cfp_tbl.columns=["School","Power Rank","Power Index","Off PPG","Def PPG","Net PPG","CFP Seed","Δ Seed−Rank"]
        st.dataframe(cfp_tbl.style.format({"Power Index":"{:.3f}","Off PPG":"{:.1f}","Def PPG":"{:.1f}","Net PPG":"{:.1f}","Δ Seed−Rank":"{:+.0f}"}),
            use_container_width=True,hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6: METHODOLOGY
# ══════════════════════════════════════════════════════════════════════════════
if page == "Methodology":
    c1,c2=st.columns(2)
    with c1:
        st.markdown("### V2 — 2026 Forward-Looking Index")
        st.markdown("""
Nine components, each 0–100, weighted into the Power Index. Built to answer
*"who will be good in 2026?"*, not *"who was good in 2025?"* — roster construction
(returning production, the QB, net portal flow, recruiting) carries the most weight.

| Component | Weight | Source |
|-----------|--------|--------|
| Prior-Year Quality | 20% | 2025 EPA/success-rate/explosiveness (CFBD advanced) |
| Returning Production | 20% | Player-level 2025 output minus portal/NFL exits |
| QB Room | 14% | Verified 2026 starters scored on real 2025 lines |
| **Portal Net** | 13% | **Arrivals minus departures**, position-weighted, all 4,400+ moves |
| Recruiting/Talent | 11% | 2022–2026 class ranks + points |
| Coaching Continuity | 6% | HC/OC/DC retention + scheme changes |
| **Conference Strength** | 6% | Mean prior-year quality of league mates |
| **Momentum / Buzz** | 6% | 2025 wins vs expected + recruiting trend + portal buzz |
| Schedule Strength | 4% | Avg opponent rating + road-game rate |

**Momentum/Buzz** is the model's "hype" signal, but built from measurable things:
teams that beat their expected-win profile, are trending up on the recruiting trail,
and won the portal offseason.

**Game predictions** use a schedule-independent *team strength rating* (schedule &
conference excluded, weights renormalized), so a brutal slate never makes a team
"better" at beating a specific opponent:
`P(A) = 1/(1+e^{-0.1(S_A − S_B + HFA)})`, HFA = 2.7 (4.0 for elite venues).
        """)
        st.markdown("### V1 — 2025 Efficiency Index")
        st.markdown("""
Six per-play efficiency metrics, z-scored and weighted (Off Eff 30%, Explosive 20%,
Def Eff −25%, Havoc 10%, Net PPG 10%, Net Yds 5%). Validated: **9/11 CFP bracket
games** correct, champion called before the playoff.
        """)
    with c2:
        st.markdown("### Data Files Status")
        files=[
            ("cfb_combined_data.xlsx","2025 base stats (V1)","Required"),
            ("data/processed/cfb_power_index_v2.csv","V2 model output","Run model_v2.py"),
            ("data/raw/2025_team_advanced_season_stats.csv","Prior-year quality (EPA)","Important"),
            ("data/raw/2026_returning_production.csv","Returning production","Important"),
            ("data/raw/2026_qb_starters.csv","Verified 2026 QBs (all 139)","Important"),
            ("data/raw/2026_transfer_portal_cfbd.csv","Full portal (4,400+ moves)","Important"),
            ("data/raw/2026_coaches.csv","Coaching continuity","Important"),
            ("data/raw/2022_2026_recruiting.csv","Recruiting talent","Important"),
            ("data/raw/2026_schedule.csv","Schedule + venues","Important"),
            ("data/raw/2025_records.csv","2025 records + expected wins","Important"),
            ("data/raw/2025_player_stats.csv","Player stats → depth charts","Important"),
        ]
        frows=[{"File":os.path.basename(f),"Feeds":d,"Status":"✅" if os.path.exists(f) else "⬜","Priority":p}
               for f,d,p in files]
        st.dataframe(pd.DataFrame(frows),use_container_width=True,hide_index=True)

        st.markdown("#### Depth Charts & All-Americans")
        st.markdown("""
- **Depth chart** = each team's 2025 producers, minus everyone who left via the
  portal, plus portal arrivals (with the stats they bring from their old school).
- **★ PI All-American** = top-5 nationally at the position by 2025 production —
  a model award, derived purely from the stat feed.
- OL isn't shown individually because no public per-lineman stat feed exists.
- Coverage report: `data/processed/coverage_report.csv` flags exactly which
  components are real data vs neutral-50 filler for every team.
        """)
    st.markdown("---")
    st.markdown('<small style="color:#4a4e6a">CFB Power Index · Andrew White · MSBA, UT Austin McCombs · Not affiliated with ESPN, 247Sports, or NCAA</small>',unsafe_allow_html=True)


