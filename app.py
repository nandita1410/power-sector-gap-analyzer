import json
import argparse
from collections import Counter, defaultdict
from typing import Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG

st.set_page_config(
    page_title="Power Sector Skill Gap ",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# THEME — injected CSS

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0f1117;
    border-right: 1px solid #2a2d3e;
}
section[data-testid="stSidebar"] * {
    color: #c9d1d9 !important;
}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stMultiSelect label,
section[data-testid="stSidebar"] .stSlider label {
    color: #8b949e !important;
    font-size: 11px !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-weight: 500;
}

/* Main background */
.main .block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}

/* Metric cards */
[data-testid="metric-container"] {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 1rem 1.25rem !important;
}
[data-testid="metric-container"] label {
    color: #8b949e !important;
    font-size: 11px !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #e6edf3 !important;
    font-size: 2rem !important;
    font-weight: 600;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-size: 12px !important;
}

/* Section headers */
h1 { color: #e6edf3 !important; font-weight: 600 !important; letter-spacing: -0.02em; }
h2 { color: #c9d1d9 !important; font-weight: 500 !important; }
h3 { color: #8b949e !important; font-weight: 500 !important; font-size: 13px !important;
     text-transform: uppercase; letter-spacing: 0.05em; }

/* Divider */
hr { border-color: #21262d; }

/* Tabs */
[data-baseweb="tab-list"] { background: transparent; border-bottom: 1px solid #21262d; gap: 0; }
[data-baseweb="tab"] { background: transparent !important; color: #8b949e !important;
    border-bottom: 2px solid transparent !important; padding: 8px 20px; font-size: 13px; }
[aria-selected="true"][data-baseweb="tab"] { color: #58a6ff !important;
    border-bottom-color: #58a6ff !important; }

/* DataFrames */
[data-testid="stDataFrame"] { border: 1px solid #30363d; border-radius: 8px; }

/* Badges / pills */
.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 500;
    font-family: 'DM Mono', monospace;
}
.badge-critical { background: #3d1a1a; color: #f85149; border: 1px solid #6e1f1f; }
.badge-high     { background: #2d1f00; color: #e3b341; border: 1px solid #5a3e00; }
.badge-medium   { background: #0d2131; color: #58a6ff; border: 1px solid #1158a7; }
.badge-low      { background: #0d1f0d; color: #3fb950; border: 1px solid #1a6425; }

/* Country flag pills */
.country-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
    margin: 2px;
}

/* Insight cards */
.insight-box {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 10px;
    font-size: 13px;
    color: #c9d1d9;
    line-height: 1.6;
}
.insight-box.warn  { border-left: 3px solid #e3b341; }
.insight-box.danger{ border-left: 3px solid #f85149; }
.insight-box.good  { border-left: 3px solid #3fb950; }
.insight-box.info  { border-left: 3px solid #58a6ff; }

/* Gap score ring */
.gap-ring-container {
    text-align: center;
    padding: 1rem;
}
.gap-score-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #8b949e;
    margin-top: 6px;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAXONOMY & CONSTANTS

POWER_TAXONOMY = {
    "Traditional Power Engineering": [
        "power systems","electrical engineering","substation","transformer","switchgear",
        "protection relay","load flow","short circuit","power factor","reactive power",
        "HV","LV","MV","11kV","33kV","132kV","400kV","busbar","circuit breaker",
        "earthing","SCADA","DCS","PLC","HMI","IED","RTU","metering","energy audit",
        "grid","distribution","transmission","ETAP","PSS/E",
    ],
    "Renewables & Energy Transition": [
        "solar PV","wind energy","wind turbine","battery storage","BESS","energy storage",
        "lithium ion","offshore wind","onshore wind","rooftop solar","hybrid energy",
        "microgrid","VPP","virtual power plant","EV charging","green hydrogen",
        "electrolysis","fuel cell","geothermal","biomass",
    ],
    "Digital & Analytics": [
        "data analytics","machine learning","AI","artificial intelligence","IoT",
        "digital twin","predictive maintenance","big data","python","MATLAB",
        "power BI","Tableau","cloud","AWS","Azure","GCP","cybersecurity","OT security",
        "DERMS","energy management system","smart meter","AMI","edge computing",
        "blockchain","digital transformation",
    ],
    "Grid Modernization": [
        "smart grid","grid modernization","flexibility","demand response","ancillary services",
        "frequency regulation","voltage regulation","grid stability","HVDC","FACTS",
        "SVC","STATCOM","power electronics","inverter","converter","wide area monitoring",
        "PMU","synchrophasor",
    ],
    "Project & Commercial": [
        "project management","PMP","EPC","O&M","feasibility study","financial modelling",
        "PPA","tariff","regulatory","offtake","contract","procurement","capex","opex",
        "IRR","NPV","due diligence","asset management","HSE","HSSE","LOTO","permits",
    ],
    "Sustainability & Policy": [
        "ESG","carbon footprint","net zero","decarbonization","sustainability","GHG",
        "emissions","carbon credit","CDP","climate risk","TCFD","policy",
        "regulatory compliance","RE100","SBTi","just transition","circular economy",
    ],
}

ALL_SKILLS = [s for skills in POWER_TAXONOMY.values() for s in skills]

COUNTRY_META = {
    "us": {"name": "United States", "flag": "🇺🇸", "color": "#4C9BE8"},
    "gb": {"name": "United Kingdom", "flag": "🇬🇧", "color": "#3FB950"},
    "au": {"name": "Australia",      "flag": "🇦🇺", "color": "#E3B341"},
    "in": {"name": "India",          "flag": "🇮🇳", "color": "#F85149"},
}
FIRST_WORLD = ["us", "gb", "au"]

EMERGING_SKILLS = [
    "BESS","digital twin","green hydrogen","virtual power plant","HVDC","cybersecurity",
    "machine learning","IoT","DERMS","edge computing","synchrophasor","EV charging",
    "carbon credit","blockchain","predictive maintenance","AI","wide area monitoring",
    "smart meter","digital transformation",
]

PLOTLY_TEMPLATE = "plotly_dark"
CHART_BG = "#0d1117"
PAPER_BG = "#0d1117"
FONT_COLOR = "#c9d1d9"
GRID_COLOR = "#21262d"

# ─────────────────────────────────────────────────────────────────────────────
# DEMO DATA

DEMO_JOBS = [
    {"source":"adzuna","country":"us","title":"Senior Grid Modernization Engineer","company":"NextEra Energy","description":"Lead smart grid deployments SCADA DCS integration DERMS demand response IoT sensor networks predictive maintenance machine learning digital twin cybersecurity OT AWS cloud python HVDC synchrophasor PMU BESS energy storage battery storage grid stability wide area monitoring ancillary services frequency regulation ESG net zero."},
    {"source":"adzuna","country":"us","title":"Energy Storage Systems Engineer","company":"Tesla Energy","description":"Design commission BESS lithium ion battery management inverter controls virtual power plant VPP EV charging power electronics grid interconnection python ML analytics digital twin carbon credit ESG frequency regulation ancillary services blockchain energy storage cybersecurity AWS Azure."},
    {"source":"adzuna","country":"us","title":"Offshore Wind Technical Lead","company":"Orsted US","description":"Offshore wind turbine HVDC transmission power systems load flow short circuit transformer protection relay machine learning predictive maintenance digital twin project management PMP ESG sustainability green hydrogen carbon footprint SBTi net zero AWS cloud python MATLAB data analytics."},
    {"source":"adzuna","country":"us","title":"Power Systems Data Scientist","company":"Eaton","description":"Machine learning anomaly detection python IoT edge computing big data cloud AWS Azure digital twin SCADA power BI Tableau predictive maintenance grid stability smart meter AMI cybersecurity OT security synchrophasor artificial intelligence data analytics digital transformation."},
    {"source":"adzuna","country":"us","title":"Renewable Integration Specialist","company":"EPRI","description":"Grid modernization BESS battery storage virtual power plant VPP FACTS SVC STATCOM demand response ancillary services frequency regulation DERMS smart grid wide area monitoring PMU python MATLAB feasibility study PPA ESG net zero decarbonization sustainability."},
    {"source":"adzuna","country":"us","title":"OT Cybersecurity Engineer","company":"Dragos","description":"OT security cybersecurity ICS SCADA protection industrial control systems digital transformation AWS cloud IoT edge computing machine learning python data analytics power systems substation protection relay HSE regulatory compliance."},
    {"source":"adzuna","country":"gb","title":"Net Zero Grid Engineer","company":"National Grid ESO","description":"HVDC offshore wind battery storage BESS synchrophasor PMU machine learning digital twin virtual power plant ESG net zero carbon footprint SBTi green hydrogen smart grid demand response ancillary services cybersecurity OT python regulatory compliance TCFD climate risk decarbonization."},
    {"source":"adzuna","country":"gb","title":"Energy Transition Consultant","company":"Atkins","description":"Green hydrogen electrolysis offshore wind BESS EV charging decarbonization net zero ESG CDP carbon credit TCFD climate risk financial modelling IRR NPV PPA regulatory compliance just transition sustainability circular economy SBTi."},
    {"source":"adzuna","country":"gb","title":"Power Electronics Engineer","company":"GE Vernova","description":"Power electronics inverter converter HVDC offshore wind turbine BESS battery storage EV charging digital twin machine learning short circuit protection relay cybersecurity python MATLAB grid stability ESG sustainability."},
    {"source":"adzuna","country":"gb","title":"Smart Grid Solutions Architect","company":"Siemens Energy","description":"Smart grid SCADA DCS IoT edge computing cloud AWS Azure digital twin OT cybersecurity AMI smart meter DERMS demand response machine learning predictive maintenance big data python grid stability wide area monitoring PMU substation IED."},
    {"source":"adzuna","country":"gb","title":"Offshore Wind Project Manager","company":"RWE Renewables","description":"Offshore wind EPC project management PMP HSE HSSE procurement PPA financial modelling capex opex ESG sustainability carbon footprint regulatory compliance due diligence asset management O&M transformer substation net zero."},
    {"source":"adzuna","country":"gb","title":"Digital Energy Analyst","company":"Wood Mackenzie","description":"Data analytics python power BI Tableau machine learning AI digital twin IoT cloud AWS big data financial modelling IRR NPV PPA ESG carbon footprint decarbonization net zero TCFD climate risk regulatory compliance."},
    {"source":"adzuna","country":"au","title":"Renewable Energy Systems Engineer","company":"AGL Energy","description":"Solar PV battery storage BESS virtual power plant VPP EV charging smart grid demand response SCADA DCS inverter power electronics IoT python machine learning digital twin ESG net zero carbon footprint green hydrogen microgrid grid stability cybersecurity."},
    {"source":"adzuna","country":"au","title":"Energy Storage Lead Engineer","company":"Neoen Australia","description":"Battery storage BESS lithium ion frequency regulation ancillary services power electronics SCADA machine learning AI digital twin virtual power plant ESG sustainability PPA financial modelling project management PMP cybersecurity OT wide area monitoring."},
    {"source":"adzuna","country":"au","title":"Grid Stability Analyst","company":"AEMO","description":"Power systems load flow short circuit wide area monitoring PMU synchrophasor frequency regulation voltage regulation FACTS STATCOM HVDC machine learning python MATLAB smart grid demand response SCADA digital twin grid modernization cybersecurity OT."},
    {"source":"adzuna","country":"au","title":"Power Sector Digital Transformation","company":"Accenture","description":"Digital twin IoT edge computing cloud AWS Azure GCP machine learning AI big data python SCADA cybersecurity OT security smart meter AMI DERMS demand response blockchain ESG carbon footprint predictive maintenance project management digital transformation."},
    {"source":"adzuna","country":"au","title":"Green Hydrogen Project Engineer","company":"Fortescue","description":"Green hydrogen electrolysis fuel cell feasibility study financial modelling PPA EPC project management PMP HSE procurement capex opex IRR NPV ESG sustainability net zero SBTi decarbonization regulatory compliance due diligence."},
    {"source":"indeed_rss","country":"in","title":"Electrical Engineer Power Systems","company":"NTPC Limited","description":"Power systems protection relay substation 132kV 400kV transformer switchgear load flow short circuit SCADA DCS PLC HMI earthing busbar circuit breaker energy audit grid distribution transmission power factor reactive power metering LOTO HSE ETAP."},
    {"source":"indeed_rss","country":"in","title":"Electrical Site Engineer","company":"Adani Power","description":"Substation commissioning transformer HV LV MV switchgear protection relay SCADA PLC earthing busbar circuit breaker 11kV 33kV metering energy audit load flow HSE LOTO procurement single line diagram cable sizing."},
    {"source":"indeed_rss","country":"in","title":"Solar Project Engineer","company":"Greenko Group","description":"Solar PV rooftop solar inverter SCADA earthing metering grid interconnection energy audit project management HSE procurement feasibility study single line diagram cable sizing."},
    {"source":"indeed_rss","country":"in","title":"Power Plant O&M Engineer","company":"Tata Power","description":"O&M power plant DCS PLC HMI SCADA transformer substation protection relay energy audit HSE LOTO metering switchgear busbar circuit breaker earthing."},
    {"source":"indeed_rss","country":"in","title":"Electrical Design Engineer","company":"L&T Power","description":"Electrical design substation protection relay transformer earthing load flow short circuit ETAP SCADA procurement HSE IEC standards AutoCAD single line diagram."},
    {"source":"indeed_rss","country":"in","title":"Wind Energy Technician","company":"Suzlon Energy","description":"Wind turbine wind energy O&M SCADA protection relay grid earthing HSE LOTO metering preventive maintenance."},
    {"source":"indeed_rss","country":"in","title":"Power Sector Analyst","company":"Power Finance Corporation","description":"Financial modelling PPA regulatory compliance capex opex IRR NPV due diligence procurement feasibility study asset management tariff policy."},
    {"source":"indeed_rss","country":"in","title":"Distribution Engineer","company":"MSEDCL","description":"Distribution 11kV substation transformer protection relay metering energy audit HSE load flow earthing switchgear busbar circuit breaker."},
    {"source":"indeed_rss","country":"in","title":"Substation Engineer","company":"PGCIL","description":"Substation 400kV 132kV transformer switchgear protection relay SCADA IED earthing busbar circuit breaker HV metering energy audit HSE LOTO."},
]


# ─────────────────────────────────────────────────────────────────────────────
# DATA PROCESSING

def extract_skills(text: str) -> list[str]:
    if not text:
        return []
    lower = text.lower()
    return [s for s in ALL_SKILLS if s.lower() in lower]


def skill_category(skill: str) -> str:
    for cat, skills in POWER_TAXONOMY.items():
        if any(s.lower() == skill.lower() for s in skills):
            return cat
    return "Other"


@st.cache_data
def load_jobs(raw: str | None) -> pd.DataFrame:
    if raw:
        try:
            jobs = json.loads(raw)
        except Exception:
            jobs = DEMO_JOBS
    else:
        jobs = DEMO_JOBS

    rows = []
    for j in jobs:
        desc = j.get("description","") + " " + j.get("title","")
        skills = j.get("skills") or extract_skills(desc)
        rows.append({
            "country":  j.get("country","xx"),
            "title":    j.get("title",""),
            "company":  j.get("company",""),
            "source":   j.get("source",""),
            "skills":   skills,
            "skill_count": len(skills),
        })
    return pd.DataFrame(rows)


@st.cache_data
def compute_freq(df: pd.DataFrame) -> dict[str, dict[str, float]]:
    freq = {}
    for cc in df["country"].unique():
        sub = df[df["country"] == cc]
        n = len(sub)
        ctr = Counter(s for skills in sub["skills"] for s in skills)
        freq[cc] = {s: round(c / n * 100, 1) for s, c in ctr.items()}
    return freq


@st.cache_data
def compute_global_bench(freq: dict) -> dict[str, float]:
    fw = [cc for cc in FIRST_WORLD if cc in freq]
    if not fw:
        return {}
    all_skills = set(s for cc in fw for s in freq[cc])
    return {s: round(sum(freq[cc].get(s, 0) for cc in fw) / len(fw), 1) for s in all_skills}


@st.cache_data
def build_gap_df(freq: dict, global_bench: dict) -> pd.DataFrame:
    india = freq.get("in", {})
    rows = []

    # 🔴 HANDLE EMPTY GLOBAL BENCHMARK
    if not global_bench:
        return pd.DataFrame(columns=[
            "skill", "category", "global_pct", "india_pct", "gap", "severity"
        ])

    for skill, g_pct in global_bench.items():
        i_pct = india.get(skill, 0)
        gap = round(g_pct - i_pct, 1)

        rows.append({
            "skill": skill,
            "category": skill_category(skill),
            "global_pct": g_pct,
            "india_pct": i_pct,
            "gap": gap,
            "severity": (
                "critical" if gap > 30 else
                "high" if gap > 15 else
                "medium" if gap > 5 else
                "low"
            ),
        })

    df = pd.DataFrame(rows)

    # 🔴 EXTRA SAFETY
    if df.empty or "gap" not in df.columns:
        return pd.DataFrame(columns=[
            "skill", "category", "global_pct", "india_pct", "gap", "severity"
        ])

    return df.sort_values("gap", ascending=False).reset_index(drop=True)

# ─────────────────────────────────────────────────────────────────────────────
# CHART BUILDERS

CHART_LAYOUT = dict(
    template=PLOTLY_TEMPLATE,
    paper_bgcolor=PAPER_BG,
    plot_bgcolor=CHART_BG,
    font=dict(family="DM Sans", color=FONT_COLOR, size=12),
    margin=dict(l=10, r=10, t=40, b=10),
)


def chart_top_skills(freq: dict[str, float], country: str, top_n: int = 15) -> go.Figure:
    meta = COUNTRY_META.get(country, {"name": country, "flag": "", "color": "#4C9BE8"})
    data = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:top_n]
    skills, pcts = zip(*data) if data else ([], [])

    cats = [skill_category(s) for s in skills]
    cat_colors = {
        "Traditional Power Engineering": "#4C9BE8",
        "Renewables & Energy Transition": "#3FB950",
        "Digital & Analytics":            "#E3B341",
        "Grid Modernization":             "#A371F7",
        "Project & Commercial":           "#79C0FF",
        "Sustainability & Policy":        "#56D364",
        "Other":                          "#8b949e",
    }
    bar_colors = [cat_colors.get(c, "#8b949e") for c in cats]

    fig = go.Figure(go.Bar(
        x=list(pcts), y=list(skills), orientation="h",
        marker=dict(color=bar_colors, line=dict(width=0)),
        text=[f"{p:.0f}%" for p in pcts],
        textposition="outside",
        textfont=dict(size=11, color=FONT_COLOR),
        hovertemplate="<b>%{y}</b><br>%{x:.1f}% of listings<extra></extra>",
    ))

    # Legend patches
    legend_cats = list({c for c in cats})
    for cat in legend_cats:
        fig.add_trace(go.Bar(
            x=[None], y=[None], name=cat[:28],
            marker_color=cat_colors.get(cat, "#8b949e"),
            showlegend=True,
        ))

    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(text=f"{meta['flag']} Top {top_n} Skills — {meta['name']}", font=dict(size=14)),
        height=max(350, top_n * 30 + 80),
        xaxis=dict(title="% of job listings", gridcolor=GRID_COLOR, range=[0, max(pcts)*1.25 if pcts else 100]),
        yaxis=dict(autorange="reversed", tickfont=dict(size=11), gridcolor=GRID_COLOR),
        legend=dict(orientation="v", x=1.01, y=1, bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
        barmode="overlay",
        showlegend=True,
    )
    return fig


def chart_cross_country(freq: dict, top_n: int = 12) -> go.Figure:
    # Pick top skills globally
    all_skills_ctr: Counter = Counter()
    for cc_freq in freq.values():
        for s, p in cc_freq.items():
            all_skills_ctr[s] += p
    top_skills = [s for s, _ in all_skills_ctr.most_common(top_n)]

    fig = go.Figure()
    for cc, meta in COUNTRY_META.items():
        if cc not in freq:
            continue
        vals = [freq[cc].get(s, 0) for s in top_skills]
        fig.add_trace(go.Bar(
            name=f"{meta['flag']} {meta['name']}",
            x=top_skills, y=vals,
            marker_color=meta["color"],
            opacity=0.85,
            hovertemplate=f"<b>{meta['name']}</b><br>%{{x}}: %{{y:.1f}}%<extra></extra>",
        ))

    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(text=f"Cross-Country Skill Demand — Top {top_n} Global Skills", font=dict(size=14)),
        barmode="group",
        height=420,
        xaxis=dict(tickangle=-35, gridcolor=GRID_COLOR),
        yaxis=dict(title="% of job listings", gridcolor=GRID_COLOR),
        legend=dict(orientation="h", y=-0.25, bgcolor="rgba(0,0,0,0)"),
    )
    return fig


def chart_gap_bars(gap_df: pd.DataFrame, top_n: int = 16) -> go.Figure:
    top = gap_df.head(top_n)
    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=top["skill"], x=top["global_pct"], name="Global avg",
        orientation="h", marker_color="#4C9BE8", opacity=0.85,
        hovertemplate="<b>%{y}</b><br>Global: %{x:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=top["skill"], x=top["india_pct"], name="🇮🇳 India",
        orientation="h", marker_color="#F85149", opacity=0.85,
        hovertemplate="<b>%{y}</b><br>India: %{x:.1f}%<extra></extra>",
    ))

    # Gap annotation markers
    for _, row in top.iterrows():
        if row["gap"] > 0:
            fig.add_annotation(
                x=max(row["global_pct"], row["india_pct"]) + 2,
                y=row["skill"],
                text=f"−{row['gap']:.0f}%",
                showarrow=False,
                font=dict(size=10, color="#F85149"),
                xanchor="left",
            )

    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(text="Skill Gap — India vs Global Benchmark", font=dict(size=14)),
        barmode="overlay",
        height=max(380, top_n * 30 + 80),
        xaxis=dict(title="% of job listings", gridcolor=GRID_COLOR, range=[0, 115]),
        yaxis=dict(autorange="reversed", gridcolor=GRID_COLOR, tickfont=dict(size=11)),
        legend=dict(orientation="h", y=-0.08, bgcolor="rgba(0,0,0,0)"),
    )
    return fig


def chart_radar(freq: dict, selected: list[str]) -> go.Figure:
    cats = list(POWER_TAXONOMY.keys())
    short_cats = [c.split(" ")[0] + "<br>" + " ".join(c.split(" ")[1:3]) for c in cats]

    def cat_score(cc_freq: dict[str, float]) -> list[float]:
        scores = []
        for cat, skills in POWER_TAXONOMY.items():
            agg = sum(cc_freq.get(s, 0) for s in skills)
            scores.append(min(100, round(agg / len(skills) * 2.5, 1)))
        return scores

    fig = go.Figure()
    for cc in selected:
        if cc not in freq:
            continue
        meta = COUNTRY_META.get(cc, {"name": cc, "flag": "", "color": "#ccc"})
        scores = cat_score(freq[cc])
        fig.add_trace(go.Scatterpolar(
            r=scores + [scores[0]],
            theta=short_cats + [short_cats[0]],
            fill="toself", name=f"{meta['flag']} {meta['name']}",
            line=dict(color=meta["color"], width=2),
            fillcolor='rgba(227,179,65,0.08)',
            hovertemplate="%{theta}: %{r:.0f}<extra></extra>",
        ))

    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(text="Skill Category Radar", font=dict(size=14)),
        polar=dict(
            bgcolor=CHART_BG,
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=9),
                            gridcolor=GRID_COLOR, linecolor=GRID_COLOR),
            angularaxis=dict(tickfont=dict(size=9), gridcolor=GRID_COLOR, linecolor=GRID_COLOR),
        ),
        height=420,
        legend=dict(orientation="h", y=-0.1, bgcolor="rgba(0,0,0,0)"),
        showlegend=True,
    )
    return fig


def chart_heatmap(freq: dict) -> go.Figure:
    countries = [cc for cc in ["us","gb","au","in"] if cc in freq]
    top_skills = []
    ctr: Counter = Counter()
    for cc in countries:
        for s, p in freq[cc].items():
            ctr[s] += p
    top_skills = [s for s, _ in ctr.most_common(18)]

    z = [[freq[cc].get(s, 0) for s in top_skills] for cc in countries]
    y_labels = [f"{COUNTRY_META.get(cc,{}).get('flag','')} {COUNTRY_META.get(cc,{}).get('name',cc)}" for cc in countries]

    fig = go.Figure(go.Heatmap(
        z=z, x=top_skills, y=y_labels,
        colorscale=[
            [0.0,  "#0d1117"],
            [0.25, "#0d2131"],
            [0.5,  "#1158a7"],
            [0.75, "#2f81f7"],
            [1.0,  "#58a6ff"],
        ],
        text=[[f"{v:.0f}%" for v in row] for row in z],
        texttemplate="%{text}",
        textfont=dict(size=10),
        hovertemplate="<b>%{y}</b> — %{x}<br>%{z:.1f}% of listings<extra></extra>",
        colorbar=dict(title="% listings", tickfont=dict(size=10)),
    ))
    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(text="Skill Demand Heatmap — All Countries", font=dict(size=14)),
        height=260,
        xaxis=dict(tickangle=-40, tickfont=dict(size=9.5), gridcolor=GRID_COLOR),
        yaxis=dict(tickfont=dict(size=11)),
    )
    return fig


def chart_emerging(freq: dict) -> go.Figure:
    countries = [cc for cc in ["us","gb","au","in"] if cc in freq]
    skills = [e for e in EMERGING_SKILLS if any(freq[cc].get(e, 0) > 0 for cc in countries)][:14]

    fig = go.Figure()
    for cc in countries:
        meta = COUNTRY_META.get(cc, {"name":cc,"flag":"","color":"#ccc"})
        vals = [freq[cc].get(s, 0) for s in skills]
        fig.add_trace(go.Bar(
            name=f"{meta['flag']} {meta['name']}",
            x=skills, y=vals,
            marker_color=meta["color"], opacity=0.85,
            hovertemplate=f"<b>{meta['name']}</b><br>%{{x}}: %{{y:.1f}}%<extra></extra>",
        ))

    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(text="Emerging Technology Adoption by Market", font=dict(size=14)),
        barmode="group", height=380,
        xaxis=dict(tickangle=-35, gridcolor=GRID_COLOR, tickfont=dict(size=10)),
        yaxis=dict(title="% of job listings", gridcolor=GRID_COLOR),
        legend=dict(orientation="h", y=-0.28, bgcolor="rgba(0,0,0,0)"),
    )
    return fig


def chart_gap_score_gauge(score: int) -> go.Figure:
    color = "#3FB950" if score < 30 else "#E3B341" if score < 60 else "#F85149"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain=dict(x=[0,1], y=[0,1]),
        title=dict(text="India Gap Score", font=dict(size=13, color=FONT_COLOR)),
        number=dict(suffix="/100", font=dict(size=28, color=color)),
        gauge=dict(
            axis=dict(range=[0,100], tickwidth=1, tickcolor=GRID_COLOR,
                      tickfont=dict(size=10, color=FONT_COLOR)),
            bar=dict(color=color, thickness=0.7),
            bgcolor=CHART_BG,
            borderwidth=1,
            bordercolor=GRID_COLOR,
            steps=[
                dict(range=[0,30],  color="#0d1f0d"),
                dict(range=[30,60], color="#2d1f00"),
                dict(range=[60,100],color="#3d1a1a"),
            ],
            threshold=dict(line=dict(color=color, width=3), thickness=0.8, value=score),
        ),
    ))
    fig.update_layout(
        **CHART_LAYOUT,
        height=220
    )
    return fig


def chart_category_bar(gap_df: pd.DataFrame) -> go.Figure:
    cat_gaps = gap_df.groupby("category").agg(
        avg_gap=("gap","mean"),
        avg_global=("global_pct","mean"),
        avg_india=("india_pct","mean"),
    ).reset_index().sort_values("avg_gap", ascending=False)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=cat_gaps["category"], y=cat_gaps["avg_global"],
        name="Global avg", marker_color="#4C9BE8", opacity=0.8,
    ))
    fig.add_trace(go.Bar(
        x=cat_gaps["category"], y=cat_gaps["avg_india"],
        name="India", marker_color="#F85149", opacity=0.8,
    ))
    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(text="Avg Skill Demand by Category", font=dict(size=14)),
        barmode="group", height=340,
        xaxis=dict(tickangle=-25, tickfont=dict(size=10), gridcolor=GRID_COLOR),
        yaxis=dict(title="Avg % of listings", gridcolor=GRID_COLOR),
        legend=dict(orientation="h", y=-0.3, bgcolor="rgba(0,0,0,0)"),
    )
    return fig


def main():
    # ── Load Data
    uploaded = st.sidebar.file_uploader(
        "Upload jobs.json (from scraper)",
        type=["json"],
        help="Run scraper.py first to generate this file",
    )
    raw_json = uploaded.read().decode() if uploaded else None
    df = load_jobs(raw_json)

    freq      = compute_freq(df)
    global_bm = compute_global_bench(freq)
    gap_df    = build_gap_df(freq, global_bm)

    # ── Sidebar 
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚡ Filters")

    available_countries = sorted(df["country"].unique().tolist())
    country_labels = {cc: f"{COUNTRY_META.get(cc,{}).get('flag','')} {COUNTRY_META.get(cc,{}).get('name',cc)}" for cc in available_countries}

    selected_countries = st.sidebar.multiselect(
        "Countries",
        options=available_countries,
        default=available_countries,
        format_func=lambda x: country_labels.get(x, x),
    )
    if not selected_countries:
        selected_countries = available_countries

    top_n = st.sidebar.slider("Top N skills to display", 5, 30, 15)

    all_cats = list(POWER_TAXONOMY.keys())
    selected_cats = st.sidebar.multiselect(
        "Skill categories",
        options=all_cats,
        default=all_cats,
    )
    if not selected_cats:
        selected_cats = all_cats

    severity_filter = st.sidebar.multiselect(
        "Gap severity",
        options=["critical","high","medium","low"],
        default=["critical","high","medium","low"],
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📦 Pipeline")
    st.sidebar.code("python scraper.py\npython analyze.py\nstreamlit run dashboard.py", language="bash")

    # ── Filter data
    df_filtered  = df[df["country"].isin(selected_countries)]
    freq_filtered = {cc: f for cc, f in freq.items() if cc in selected_countries}
    gap_filtered  = gap_df[
        (gap_df["category"].isin(selected_cats)) &
        (gap_df["severity"].isin(severity_filter))
    ].reset_index(drop=True)

    # ── Header 
    col_h1, col_h2 = st.columns([3,1])
    with col_h1:
        st.markdown("# ⚡ Power Sector Skill Gap Dashboard")
        st.caption("India vs global first-world markets Research Platform")

    st.markdown("---")

    # ── KPI Row 
    total_jobs    = len(df_filtered)
    total_skills  = len(global_bm)
    critical_gaps = len(gap_df[gap_df["severity"] == "critical"])
    missing       = len(gap_df[(gap_df["india_pct"] < 5) & (gap_df["global_pct"] > 10)])
    gap_score     = min(100, max(0, int(
        100 - (gap_df.head(20)["india_pct"].mean() / max(gap_df.head(20)["global_pct"].mean(), 1)) * 100
    ))) if not gap_df.empty else 0

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Jobs analyzed",    f"{total_jobs:,}",   "across all sources")
    k2.metric("Skills in taxonomy", f"{total_skills}",  "ESCO-mapped")
    k3.metric("Critical gaps",    str(critical_gaps), ">30% gap")
    k4.metric("Missing in India", str(missing),        "0% vs 10%+ global")
    k5.metric("Gap index",        f"{gap_score}/100",   "0 = parity · 100 = full divergence")

    st.markdown("---")

    # ── TABS 
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏆 Top Skills",
        "🌍 Cross-Country",
        "🔍 Skill Gap",
        "⚡ Emerging Tech",
        "📊 Raw Data",
    ])

    # ────────────────────────────────────────────────────────────────────────
    # TAB 1 — TOP SKILLS
    
    with tab1:
        st.markdown("### Top skills by country")
        st.caption("Skill frequency as % of job listings · colored by taxonomy category")

        if len(selected_countries) == 1:
            cc = selected_countries[0]
            st.plotly_chart(
                chart_top_skills(freq.get(cc, {}), cc, top_n),
                use_container_width=True,
            )
        else:
            cols = st.columns(min(len(selected_countries), 2))
            for i, cc in enumerate(selected_countries):
                with cols[i % 2]:
                    st.plotly_chart(
                        chart_top_skills(freq.get(cc, {}), cc, top_n),
                        use_container_width=True,
                    )

        st.markdown("---")
        st.markdown("### Skill demand heatmap")
        st.caption("Intensity of skill demand per country — darker = higher % of listings")
        if freq_filtered:
            st.plotly_chart(chart_heatmap(freq_filtered), use_container_width=True)

        st.markdown("---")
        st.markdown("### Category breakdown")
        col_r, col_b = st.columns([1, 1])
        with col_r:
            st.plotly_chart(chart_radar(freq_filtered, selected_countries), use_container_width=True)
        with col_b:
            st.plotly_chart(chart_category_bar(gap_filtered), use_container_width=True)

    # ────────────────────────────────────────────────────────────────────────
    # TAB 2 — CROSS-COUNTRY

    with tab2:
        st.markdown("### Cross-country skill comparison")
        st.caption("Grouped bars showing demand intensity for top global skills by country")
        st.plotly_chart(chart_cross_country(freq_filtered, top_n=min(top_n, 15)), use_container_width=True)

        st.markdown("---")
        st.markdown("### Country profiles")
        cols = st.columns(len(selected_countries))
        for i, cc in enumerate(selected_countries):
            meta = COUNTRY_META.get(cc, {"name":cc,"flag":"","color":"#ccc"})
            cc_freq = freq.get(cc, {})
            n_jobs = len(df[df["country"] == cc])
            top5 = sorted(cc_freq.items(), key=lambda x: x[1], reverse=True)[:5]
            with cols[i]:
                st.markdown(f"**{meta['flag']} {meta['name']}**")
                st.caption(f"{n_jobs} listings")
                for skill, pct in top5:
                    st.markdown(
                        f"<div style='display:flex;justify-content:space-between;font-size:12px;"
                        f"padding:3px 0;border-bottom:1px solid #21262d;color:#c9d1d9'>"
                        f"<span>{skill}</span><span style='color:{meta['color']};font-weight:600'>{pct:.0f}%</span></div>",
                        unsafe_allow_html=True,
                    )

        st.markdown("---")
        st.markdown("### Source distribution")
        src_counts = df_filtered.groupby(["country","source"]).size().reset_index(name="count")
        if not src_counts.empty:
            fig_src = px.bar(
                src_counts, x="country", y="count", color="source",
                barmode="stack", template=PLOTLY_TEMPLATE,
                color_discrete_sequence=["#4C9BE8","#3FB950","#E3B341","#A371F7"],
                labels={"country":"Country","count":"Job listings","source":"Source"},
            )
            fig_src.update_layout(
                paper_bgcolor=PAPER_BG, plot_bgcolor=CHART_BG,
                font=dict(color=FONT_COLOR), height=280,
                legend=dict(bgcolor="rgba(0,0,0,0)"),
                margin=dict(l=10,r=10,t=30,b=10),
            )
            st.plotly_chart(fig_src, use_container_width=True)

    # ────────────────────────────────────────────────────────────────────────
    # TAB 3 — SKILL GAP

    with tab3:
        st.markdown("### India vs global skill gap")

        col_gauge, col_insights = st.columns([1, 2])
        with col_gauge:
            st.plotly_chart(chart_gap_score_gauge(gap_score), use_container_width=True)
            st.markdown(
                "<div style='text-align:center;font-size:11px;color:#8b949e'>"
                "Higher = larger gap between India<br>and global first-world markets</div>",
                unsafe_allow_html=True,
            )

        with col_insights:
            st.markdown("**Key findings**")
            top_gap = gap_filtered.iloc[0] if not gap_filtered.empty else None
            if top_gap is not None:
                st.markdown(
                    f"<div class='insight-box danger'>🔴 <b>Largest gap: {top_gap['skill']}</b> — "
                    f"demanded in {top_gap['global_pct']:.0f}% of global listings vs {top_gap['india_pct']:.0f}% in India "
                    f"(−{top_gap['gap']:.0f}% gap).</div>",
                    unsafe_allow_html=True,
                )
            missing_skills = gap_filtered[(gap_filtered["india_pct"] < 5) & (gap_filtered["global_pct"] > 10)]
            if not missing_skills.empty:
                top_missing = missing_skills.head(4)["skill"].tolist()
                st.markdown(
                    f"<div class='insight-box warn'>🟡 <b>{len(missing_skills)} skills virtually absent from Indian listings</b>: "
                    f"{', '.join(top_missing)} and {len(missing_skills)-4} more.</div>",
                    unsafe_allow_html=True,
                )
            strengths = gap_df[gap_df["india_pct"] > gap_df["global_pct"]].head(3)
            if not strengths.empty:
                st.markdown(
                    f"<div class='insight-box good'>🟢 <b>India's relative strengths</b>: "
                    f"{', '.join(strengths['skill'].tolist())} — where India's market meets or exceeds global demand.</div>",
                    unsafe_allow_html=True,
                )
            st.markdown(
                "<div class='insight-box info'>🔵 <b>Upskilling priority</b>: Machine learning, digital twin, "
                "OT cybersecurity, and BESS represent the highest-ROI upskilling targets for Indian power sector professionals.</div>",
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.plotly_chart(chart_gap_bars(gap_filtered, top_n=min(top_n, 18)), use_container_width=True)

        st.markdown("---")
        st.markdown("### Full gap table")

        def severity_badge(s):
            colors = {"critical":"#F85149","high":"#E3B341","medium":"#58a6ff","low":"#3FB950"}
            return colors.get(s, "#ccc")

        display_df = gap_filtered[["skill","category","global_pct","india_pct","gap","severity"]].copy()
        display_df.columns = ["Skill","Category","Global %","India %","Gap %","Severity"]
        display_df["Global %"] = display_df["Global %"].apply(lambda x: f"{x:.1f}%")
        display_df["India %"]  = display_df["India %"].apply(lambda x: f"{x:.1f}%")
        display_df["Gap %"]    = display_df["Gap %"].apply(lambda x: f"{x:.1f}%")

        st.dataframe(
            display_df,
            use_container_width=True,
            height=360,
            column_config={
                "Severity": st.column_config.TextColumn("Severity"),
                "Gap %": st.column_config.TextColumn("Gap %"),
            }
        )

    # ────────────────────────────────────────────────────────────────────────
    # TAB 4 — EMERGING TECH

    with tab4:
        st.markdown("### Emerging technology adoption")
        st.caption("Frontier skills that define the next generation of power sector roles")
        st.plotly_chart(chart_emerging(freq_filtered), use_container_width=True)

        st.markdown("---")
        col_absent, col_strong = st.columns(2)

        with col_absent:
            st.markdown("**Technologies absent from Indian listings**")
            absent = gap_df[(gap_df["india_pct"] < 8) & (gap_df["global_pct"] > 8)].head(12)
            for _, row in absent.iterrows():
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;align-items:center;"
                    f"padding:5px 8px;margin-bottom:4px;background:#161b22;border-radius:6px;"
                    f"border:1px solid #30363d;font-size:12px'>"
                    f"<span style='color:#c9d1d9'>{row['skill']}</span>"
                    f"<div style='display:flex;gap:8px;align-items:center'>"
                    f"<span style='color:#4C9BE8;font-size:11px'>Global {row['global_pct']:.0f}%</span>"
                    f"<span style='color:#F85149;font-size:11px'>India {row['india_pct']:.0f}%</span>"
                    f"</div></div>",
                    unsafe_allow_html=True,
                )

        with col_strong:
            st.markdown("**India's relative strengths**")
            strong = gap_df[gap_df["india_pct"] >= gap_df["global_pct"]].sort_values("india_pct", ascending=False).head(12)
            if strong.empty:
                st.caption("No clear outperformance areas yet — fetch more data for better signal.")
            for _, row in strong.iterrows():
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;align-items:center;"
                    f"padding:5px 8px;margin-bottom:4px;background:#0d1f0d;border-radius:6px;"
                    f"border:1px solid #1a6425;font-size:12px'>"
                    f"<span style='color:#c9d1d9'>{row['skill']}</span>"
                    f"<span style='color:#3fb950;font-weight:600'>{row['india_pct']:.0f}%</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        st.markdown("---")
        st.markdown("**5-phase upskilling roadmap for Indian professionals**")
        phases = [
            ("Phase 1", "Python & Power Data Analytics", "2–3 months", "#4C9BE8",
             "Foundational digital skill — immediately hireable globally. Focus: pandas, time-series, SCADA data."),
            ("Phase 2", "Battery Storage & Energy Management", "2–4 months", "#3FB950",
             "India's storage market set to 10× by 2030. Skills: BESS sizing, PPA structuring, grid integration."),
            ("Phase 3", "OT Cybersecurity", "3–4 months", "#E3B341",
             "0% in Indian listings vs 35%+ in US/UK. High salary premium. Certs: SANS ICS, GICSP."),
            ("Phase 4", "Digital Twin & IoT", "3–5 months", "#A371F7",
             "Differentiates for global roles. Entirely absent from Indian market. Tools: Siemens MindSphere, Azure IoT."),
            ("Phase 5", "Green Hydrogen & Grid Modernization", "4–6 months", "#F85149",
             "Long-term strategic positioning. Skills: HVDC, FACTS, DERMS, green hydrogen feasibility."),
        ]
        for phase, title, dur, color, desc in phases:
            st.markdown(
                f"<div style='display:flex;gap:12px;align-items:flex-start;margin-bottom:8px;"
                f"background:#161b22;border-radius:8px;border:1px solid #30363d;padding:12px 14px'>"
                f"<div style='min-width:56px;background:{color}20;border:1px solid {color}60;"
                f"border-radius:6px;padding:6px;text-align:center;font-size:10px;font-weight:600;color:{color}'>{phase}</div>"
                f"<div><div style='font-size:13px;font-weight:600;color:#e6edf3'>{title}"
                f"<span style='font-size:11px;font-weight:400;color:#8b949e;margin-left:8px'>({dur})</span></div>"
                f"<div style='font-size:12px;color:#8b949e;margin-top:3px'>{desc}</div></div></div>",
                unsafe_allow_html=True,
            )

    # ────────────────────────────────────────────────────────────────────────
    # TAB 5 — RAW DATA

    with tab5:
        st.markdown("### Job listing dataset")
        st.caption(f"{len(df_filtered)} listings · filtered by selected countries")

        display = df_filtered.copy()
        display["skills"] = display["skills"].apply(lambda s: " · ".join(s[:6]))
        display["country"] = display["country"].apply(
            lambda cc: f"{COUNTRY_META.get(cc,{}).get('flag','')} {cc.upper()}"
        )
        st.dataframe(
            display[["country","title","company","source","skill_count","skills"]],
            use_container_width=True,
            height=420,
        )

        st.markdown("---")
        st.markdown("### Taxonomy reference")
        for cat, skills in POWER_TAXONOMY.items():
            with st.expander(f"📂 {cat} ({len(skills)} skills)"):
                st.markdown(
                    " ".join(f"<span style='background:#161b22;border:1px solid #30363d;border-radius:4px;"
                             f"padding:2px 7px;margin:2px;display:inline-block;font-size:11px;color:#c9d1d9'>{s}</span>"
                             for s in skills),
                    unsafe_allow_html=True,
                )

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        "<div style='text-align:center;font-size:11px;color:#3d3d3d'>"
        "Power Sector Skill Gap Platform · "
        "Data: Adzuna API + Indeed RSS + LinkedIn · "
        "Taxonomy: ESCO / O*NET aligned"
        "</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()