import json
import re
import os
from google import genai
from pydantic import BaseModel, Field
from typing import List
from collections import Counter
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from constants import (
    POWER_TAXONOMY, ALL_SKILLS, COUNTRY_META, FIRST_WORLD,
    EMERGING_SKILLS, CAT_COLORS, DEMO_JOBS, DEMO_RESUMES
)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Power Sector Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# THEME + CHATBOT CSS
# ─────────────────────────────────────────────────────────────────────────────
with open("style.css", "r") as f:
    css = f.read()
st.markdown(f"<style>\n{css}\n</style>", unsafe_allow_html=True)


CHART_BG   = "rgba(0,0,0,0)"
PAPER_BG   = "rgba(0,0,0,0)"
FONT_COLOR = "#c9d1d9"
GRID_COLOR = "rgba(255,255,255,0.05)"
PLOTLY_TEMPLATE = "plotly_dark"

CHART_LAYOUT = dict(
    template=PLOTLY_TEMPLATE,
    paper_bgcolor=PAPER_BG,
    plot_bgcolor=CHART_BG,
    font=dict(family="DM Sans", color=FONT_COLOR, size=12),
    margin=dict(l=10, r=10, t=40, b=10),
)

# ─────────────────────────────────────────────────────────────────────────────
# CORE UTILITIES
# ─────────────────────────────────────────────────────────────────────────────

COMPILED_SKILLS = {
    s: re.compile(r'(?<![a-z0-9])' + re.escape(s.lower()) + r'(?![a-z0-9])')
    for s in ALL_SKILLS
}

def extract_skills(text: str) -> list:
    """Whole-word regex matching to avoid false positives like HV inside 'achieved'."""
    if not text:
        return []
    lower = text.lower()
    matched = [s for s, pattern in COMPILED_SKILLS.items() if pattern.search(lower)]
    return matched


def skill_category(skill: str) -> str:
    for cat, skills in POWER_TAXONOMY.items():
        if any(s.lower() == skill.lower() for s in skills):
            return cat
    return "Other"


# ─────────────────────────────────────────────────────────────────────────────
# GROQ CLIENT
# ─────────────────────────────────────────────────────────────────────────────
import groq

def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY", "")
    
    # Try fetching from session state if available
    try:
        import streamlit as st
        if not api_key and "groq_api_key" in st.session_state:
            api_key = st.session_state.groq_api_key
    except Exception:
        pass
        
    if not api_key:
        return None
        
    try:
        return groq.Groq(api_key=api_key)
    except Exception as e:
        print(f"Failed to init Groq: {e}")
        return None

@st.cache_resource
def get_rag_engine():
    try:
        from rag_engine import RAGEngine
        return RAGEngine()
    except Exception as e:
        print(f"Failed to init RAGEngine: {e}")
    return None

class ResumeSchema(BaseModel):
    experience_years: int = Field(description="Numeric total years of professional experience.")
    education: str = Field(description="The highest education degree or notable certs.")
    location: str = Field(description="Current location or city.")
    skills: List[str] = Field(description="List of technical power sector skills.")
    summary: str = Field(description="A 2-sentence summary of their profile.")


@st.cache_data(show_spinner=False)
def extract_entities_with_llm(raw_text: str):
    llm_client = get_groq_client()
    if not llm_client:
        raise ValueError("No Groq Client.")
    prompt = f"""
    You are an expert HR recruiter in the power & energy sector.
    Analyze the following resume text and extract the candidate's years of experience,
    education, location, and technical skills mapped to standard power sector terminology.
    OUTPUT STRICTLY VALID JSON EXACTLY MATCHING THIS SCHEMA:
    {{
      "experience_years": 0,
      "education": "string",
      "location": "string",
      "skills": ["string"],
      "summary": "string"
    }}

    Resume Text:
    {raw_text[:4000]}
    """
    import json
    response = llm_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.1-8b-instant",
        response_format={"type": "json_object"}
    )
    content = response.choices[0].message.content
    try:
        parsed = json.loads(content)
        return ResumeSchema(**parsed)
    except Exception:
        raise ValueError("Failed to parse via LLM")

def legacy_parse_resume_text(text: str, name: str = "Unknown") -> dict:
    skills = extract_skills(text)
    exp_match = re.search(r'(\d+)\s*(?:\+)?\s*years?', text.lower())
    exp = int(exp_match.group(1)) if exp_match else 0
    return {"name": name, "experience_years": exp, "education": "", "location": "", "skills": skills, "text": text[:500]}


def parse_resume_text(text: str, name: str = "Unknown") -> dict:
    if not text.strip():
        return {"name": name, "experience_years": 0, "education": "", "location": "", "skills": [], "text": ""}
    try:
        extracted = extract_entities_with_llm(text)
        return {
            "name": name,
            "experience_years": extracted.experience_years,
            "education": extracted.education,
            "location": extracted.location,
            "skills": extracted.skills,
            "text": text[:500]
        }
    except Exception:
        return legacy_parse_resume_text(text, name)


def parse_pdf_resume(uploaded_file) -> dict | None:
    try:
        import pdfplumber
        with pdfplumber.open(uploaded_file) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        name = uploaded_file.name.replace(".pdf", "").replace("_", " ")
        return parse_resume_text(text, name)
    except ImportError:
        st.warning("pdfplumber not installed. Run: pip install pdfplumber")
        return None
    except Exception as e:
        st.error(f"PDF parse error: {e}")
        return None

# ─────────────────────────────────────────────────────────────────────────────
# DATA PROCESSING
# ─────────────────────────────────────────────────────────────────────────────

EDUCATION_KEYWORDS = {
    "Masters & Above": [r"\bmasters\b", r"\bm\.tech\b", r"\bms\b", r"\bm\.e\.\b", r"\bphd\b", r"\bdoctorate\b", r"\bpost\s?grad\b", r"\bpostgraduate\b"],
    "Bachelors": [r"\bbachelors\b", r"\bb\.tech\b", r"\bbs\b", r"\bb\.e\.\b", r"\bb\.sc\b", r"\bdegree\b", r"\bundergraduate\b"],
    "High School / Diploma": [r"\b12th\b", r"\bdiploma\b", r"\bhigh school\b", r"\bsecondary\b"]
}

def infer_job_education(text: str) -> str:
    """Extract approximate education requirement from description text."""
    if not text: return "Not Specified"
    lower_text = text.lower()
    for ed_level, patterns in EDUCATION_KEYWORDS.items():
        if any(re.search(p, lower_text) for p in patterns):
            return ed_level
    return "Not Specified"

COUNTRY_LOCATION_KEYWORDS = {
    "us": [r"\busa\b", r"\bu\.s\.a\b", r"\bunited states\b", r"\bnew york\b", r"\btexas\b", r"\bcalifornia\b", r"\bus\b"],
    "gb": [r"\buk\b", r"\bu\.k\.\b", r"\bunited kingdom\b", r"\blondon\b", r"\bengland\b", r"\bscotland\b"],
    "au": [r"\baustralia\b", r"\bsydney\b", r"\bmelbourne\b", r"\bbrisbane\b", r"\bperth\b"],
    "in": [r"\bindia\b", r"\bbangalore\b", r"\bmumbai\b", r"\bdelhi\b", r"\bhyderabad\b", r"\bchennai\b", r"\bpune\b"]
}

OFFSHORE_PHRASES = [
    r"any other location",
    r"you will be assigned",
    r"different time zone",
    r"not hiring for india",
    r"client is from"
]

def infer_job_country(text: str, default_country: str) -> str:
    """Overrides the default posting country if actual country/city mentions are found in the description."""
    if not text: return default_country
    lower_text = text.lower()
    
    if default_country == "in":
        # 1. Check if it mentions a foreign country explicitly
        for cc, patterns in COUNTRY_LOCATION_KEYWORDS.items():
            if cc == "in": continue
            if any(re.search(p, lower_text) for p in patterns):
                return cc
                
        # 2. Check for offshore phrases
        if any(re.search(p, lower_text) for p in OFFSHORE_PHRASES):
            return "offshore"
            
        return "in"

    for cc, patterns in COUNTRY_LOCATION_KEYWORDS.items():
        if any(re.search(p, lower_text) for p in patterns):
            return cc
    return default_country

@st.cache_data
def load_demand(raw_json: str | None) -> tuple[pd.DataFrame, dict]:
    jobs = DEMO_JOBS
    if raw_json:
        try:
            jobs = json.loads(raw_json)
        except Exception:
            pass
    rows = []
    for j in jobs:
        desc = j.get("description", "") + " " + j.get("title", "")
        skills = j.get("skills") or extract_skills(desc)
        original_country = j.get("country", "xx")
        actual_country = infer_job_country(desc, original_country)
        actual_education = infer_job_education(desc)
        rows.append({
            "country":     actual_country,
            "title":       j.get("title", ""),
            "company":     j.get("company", ""),
            "source":      j.get("source", ""),
            "skills":      skills,
            "skill_count": len(skills),
            "education":   actual_education,
        })
    df = pd.DataFrame(rows)
    n = len(df)
    if n == 0:
        return df, {}
    ctr = Counter(s for skills in df["skills"] for s in skills)
    freq = {s: round(c / n * 100, 1) for s, c in ctr.items()}
    return df, freq


@st.cache_data
def load_supply(resumes_raw: list) -> tuple[pd.DataFrame, dict]:
    rows = []
    for r in resumes_raw:
        text = r.get("text", "") + " " + r.get("name", "")
        skills = r.get("skills") or extract_skills(text)
        rows.append({
            "name":             r.get("name", "Unknown"),
            "experience_years": r.get("experience_years", 0),
            "education":        r.get("education", ""),
            "location":         r.get("location", ""),
            "skills":           skills,
            "skill_count":      len(skills),
        })
    df = pd.DataFrame(rows)
    n = len(df)
    if n == 0:
        return df, {}
    ctr = Counter(s for skills in df["skills"] for s in skills)
    freq = {s: round(c / n * 100, 1) for s, c in ctr.items()}
    return df, freq


@st.cache_data
def compute_country_freq(demand_df: pd.DataFrame) -> dict:
    freq = {}
    for cc in demand_df["country"].unique():
        sub = demand_df[demand_df["country"] == cc]
        n = len(sub)
        ctr = Counter(s for skills in sub["skills"] for s in skills)
        freq[cc] = {s: round(c / n * 100, 1) for s, c in ctr.items()}
    return freq


@st.cache_data
def compute_global_bench(country_freq: dict) -> dict:
    fw = [cc for cc in FIRST_WORLD if cc in country_freq]
    if not fw:
        return {}
    all_skills = set(s for cc in fw for s in country_freq[cc])
    return {s: round(sum(country_freq[cc].get(s, 0) for cc in fw) / len(fw), 1) for s in all_skills}


@st.cache_data
def build_gap_df(demand_freq: dict, supply_freq: dict, global_bench: dict) -> pd.DataFrame:
    all_skills = set(demand_freq) | set(supply_freq)
    rows = []
    for skill in all_skills:
        d = demand_freq.get(skill, 0)
        s = supply_freq.get(skill, 0)
        g = global_bench.get(skill, 0)
        ds_gap = round(d - s, 1)
        india_global_gap = round(g - d, 1)
        rows.append({
            "skill":            skill,
            "category":         skill_category(skill),
            "demand_pct":       d,
            "supply_pct":       s,
            "global_pct":       g,
            "ds_gap":           ds_gap,
            "india_global_gap": india_global_gap,
            "ds_status": (
                "critical_gap"  if ds_gap > 30  else
                "high_gap"      if ds_gap > 15  else
                "moderate_gap"  if ds_gap > 5   else
                "surplus"       if ds_gap < -5  else
                "balanced"
            ),
            "ig_severity": (
                "critical" if india_global_gap > 30 else
                "high"     if india_global_gap > 15 else
                "medium"   if india_global_gap > 5  else
                "low"
            ),
        })
    return pd.DataFrame(rows).sort_values("demand_pct", ascending=False).reset_index(drop=True)


def generate_recommendations(gap_df, demand_freq, supply_freq, demand_df, supply_df):
    recs = []
    critical      = gap_df[gap_df["ds_gap"] > 30].head(5)
    surplus       = gap_df[gap_df["ds_gap"] < -10].head(3)
    high_d_zero_s = gap_df[(gap_df["demand_pct"] > 20) & (gap_df["supply_pct"] < 5)]

    if not critical.empty:
        skills_list = ", ".join(critical["skill"].tolist()[:4])
        recs.append({"type":"critical","icon":"🔴","title":"Immediate Training Investment Required",
            "body":(f"Critical skill gaps in {skills_list} are blocking India's power sector from global competitiveness. "
                    f"Recommendation: Partner with IITs, NITs, NPTI to launch 3–6 month certification programs. ROI: 6–12 months."),
            "action":f"Launch bootcamps for: {skills_list}"})

    if not high_d_zero_s.empty:
        skills_list = ", ".join(high_d_zero_s["skill"].tolist()[:3])
        recs.append({"type":"critical","icon":"🔴","title":"Talent Shortage — Hire Globally or Reskill",
            "body":(f"Skills like {skills_list} have high employer demand (20%+ listings) but almost zero supply in India. "
                    f"Short-term: recruit from UK/AU/Germany. Long-term: intensive 90-day reskilling programs."),
            "action":"Global hiring + internal reskilling pipeline"})

    if not surplus.empty:
        skills_list = ", ".join(surplus["skill"].tolist())
        recs.append({"type":"opportunity","icon":"🟢","title":"Export Opportunity — India Has Surplus Talent",
            "body":(f"India has more professionals with {skills_list} than domestic demand requires. "
                    f"Position India as a global talent hub — target Middle East, Southeast Asia, and Africa."),
            "action":"Market India talent surplus to GCC, SEA, Africa"})

    digital_demand = demand_freq.get("machine learning",0)+demand_freq.get("python",0)+demand_freq.get("digital twin",0)
    digital_supply = supply_freq.get("machine learning",0)+supply_freq.get("python",0)+supply_freq.get("digital twin",0)
    if digital_demand > digital_supply + 20:
        recs.append({"type":"invest","icon":"🔵","title":"Curriculum Reform — Add Digital Skills to Power Engineering",
            "body":("B.Tech/M.Tech curricula lack machine learning, digital twin, IoT. Global employers demand these in 60–80% of roles. "
                    "AICTE/UGC should mandate a 'Digital Power Engineering' module. NPTEL/Coursera can bridge the gap in 3–6 months."),
            "action":"Lobby AICTE for curriculum update + NPTEL partnerships"})

    bess_gap = gap_df[gap_df["skill"].isin(["BESS","battery storage","green hydrogen","EV charging"])]["ds_gap"].mean()
    if bess_gap > 10:
        recs.append({"type":"invest","icon":"🔵","title":"Energy Transition Skills — First Mover Advantage",
            "body":("BESS, green hydrogen, EV charging show 40–60% demand growth globally; India's supply is near zero. "
                    "Partner with OEMs (Tesla, BYD) for BESS training; tie-up with NTPC Green Energy for hydrogen."),
            "action":"OEM partnerships for BESS + hydrogen training"})

    cyber_gap = gap_df[gap_df["skill"].isin(["cybersecurity","OT security"])]["ds_gap"].mean()
    if cyber_gap > 15:
        recs.append({"type":"warn","icon":"🟡","title":"Critical Infrastructure Risk — OT Cybersecurity Deficit",
            "body":("OT/ICS cybersecurity demanded in 40%+ of US/UK listings but nearly absent in India's talent pool. "
                    "Ministry of Power + CERT-In should mandate OT cybersecurity training. Certs: GICSP, CSSA, SANS ICS."),
            "action":"Mandate GICSP certification for SCADA engineers"})

    avg_exp = supply_df["experience_years"].mean() if not supply_df.empty else 0
    if avg_exp > 0:
        recs.append({"type":"invest","icon":"🔵","title":"Compensation Strategy — Retain Upskilled Talent",
            "body":(f"Average experience in talent pool is {avg_exp:.1f} years. Upskilled professionals see 30–50% salary jumps. "
                    f"Create 'Digital Power Engineer' pay bands at 1.3–1.5× traditional rates."),
            "action":"Revise pay bands for digital-skilled power engineers"})
    return recs

# ─────────────────────────────────────────────────────────────────────────────
# CHATBOT ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def build_data_context(gap_df: pd.DataFrame, demand_freq: dict, supply_freq: dict,
                       global_bench: dict, supply_df: pd.DataFrame) -> str:
    """Serialise current dashboard state into a compact context string for the LLM."""
    top_gaps = gap_df[gap_df["ds_gap"] > 5].head(15)[
        ["skill","category","demand_pct","supply_pct","ds_gap","global_pct","india_global_gap"]
    ].to_string(index=False)

    surplus = gap_df[gap_df["ds_gap"] < -5].head(8)[["skill","demand_pct","supply_pct","ds_gap"]].to_string(index=False)

    top_demand = sorted(demand_freq.items(), key=lambda x: x[1], reverse=True)[:12]
    top_supply = sorted(supply_freq.items(), key=lambda x: x[1], reverse=True)[:12]

    talent_summary = ""
    if not supply_df.empty:
        avg_exp   = supply_df["experience_years"].mean()
        avg_skills = supply_df["skill_count"].mean()
        locations = supply_df["location"].value_counts().head(5).to_dict()
        talent_summary = (
            f"Talent pool: {len(supply_df)} professionals, avg {avg_exp:.1f} yrs exp, "
            f"avg {avg_skills:.1f} skills. Top locations: {locations}"
        )

    return f"""
=== POWER SECTOR SKILL INTELLIGENCE — LIVE DASHBOARD DATA ===

TOP DEMAND-SUPPLY GAPS (demand % - supply %):
{top_gaps}

SURPLUS SKILLS (India supply > demand):
{surplus}

TOP 12 EMPLOYER-DEMANDED SKILLS (% of job listings):
{top_demand}

TOP 12 SUPPLY-SIDE SKILLS (% of resumes):
{top_supply}

GLOBAL BENCHMARK SNAPSHOT (first-world avg demand %):
{dict(sorted(global_bench.items(), key=lambda x: x[1], reverse=True)[:10])}

{talent_summary}

TAXONOMY CATEGORIES: {list(POWER_TAXONOMY.keys())}
"""


def build_system_prompt(data_context: str) -> str:
    return f"""You are ⚡ PowerBot, an expert analyst embedded inside a Power Sector Skill Intelligence Dashboard.
You have two modes:
1. ANALYST MODE — answer questions about skill gaps, market demand, India vs global benchmarks, hiring strategy, upskilling priorities. Use the live dashboard data below to give precise, data-backed answers.
2. RESUME SCREENER MODE — when a user shares resume text or asks about their profile, analyse their skills vs the current market demand, identify gaps, score their profile, and give a personalized upskilling roadmap.

ALWAYS:
- Be concise and specific — cite actual % numbers from the data when relevant
- Use bullet points for lists, bold for key insights
- If asked about a specific skill, look it up in the data and quote the exact demand/supply/gap figures
- For resume screening: give a match score (0-100), list matched skills, missing high-demand skills, and a 3-step action plan
- Respond in a professional but conversational tone — you're a smart co-analyst, not a chatbot

NEVER:
- Make up numbers not in the data
- Give generic advice without anchoring to the dashboard data
- Be verbose — keep answers tight and scannable

{data_context}
"""

import time

def chat_with_groq(messages: list, system_prompt: str) -> str:
    llm_client = get_groq_client()
    if not llm_client:
        return "⚠️ Groq API not connected. Please enter your API Key in the sidebar."

    contents = [
        {"role": "system", "content": system_prompt}
    ]

    for msg in messages:
        role = "user" if msg["role"] == "user" else "assistant"
        contents.append({"role": role, "content": msg["content"]})

    MAX_RETRIES = 5

    for attempt in range(MAX_RETRIES):
        try:
            response = llm_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=contents,
            )
            return response.choices[0].message.content

        except Exception as e:
            error_str = str(e)

            # 🚨 Handle 429 specifically
            if "429" in error_str or "rate_limit_exceeded" in error_str.lower() or "503" in error_str:
                wait_time = 2 ** attempt
                print(f"Retry {attempt+1}: Rate limit or server busy. Waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                return f"⚠️ API error: {error_str}"

    return "⚠️ Server is busy right now. Please try again in a few seconds."

def render_chat_message(role: str, content: str):
    css_class = "chat-msg-user" if role == "user" else "chat-msg-bot"
    prefix = "" if role == "user" else "⚡ "
    # Basic markdown → html for bold and code
    content_html = content.replace("**", "<b>", 1)
    i = 0
    result = []
    bold_open = False
    code_open = False
    for char in content:
        result.append(char)

    # Simple rendering — let streamlit markdown handle it inside expander
    st.markdown(f"<div class='{css_class}'>{prefix}{content}</div>", unsafe_allow_html=True)


STARTER_PROMPTS = [
    "What are the top 5 skill gaps right now?",
    "Which skills should India prioritise for upskilling?",
    "Compare India vs UK demand for digital skills",
    "What's the demand for BESS globally?",
    "Which skills have surplus supply in India?",
    "What roles can a SCADA engineer transition to?",
]

# ─────────────────────────────────────────────────────────────────────────────
# CHART BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

def chart_top_skills(cc_freq: dict, country: str, top_n: int = 15) -> go.Figure:
    meta = COUNTRY_META.get(country, {"name": country, "flag": "", "color": "#4C9BE8"})
    data = sorted(cc_freq.items(), key=lambda x: x[1], reverse=True)[:top_n]
    if not data:
        return go.Figure()
    skills, pcts = zip(*data)
    cats = [skill_category(s) for s in skills]
    bar_colors = [CAT_COLORS.get(c, "#8b949e") for c in cats]
    fig = go.Figure(go.Bar(
        x=list(pcts), y=list(skills), orientation="h",
        marker=dict(color=bar_colors, line=dict(width=0)),
        text=[f"{p:.0f}%" for p in pcts], textposition="outside",
        textfont=dict(size=11, color=FONT_COLOR),
        hovertemplate="<b>%{y}</b><br>%{x:.1f}% of listings<extra></extra>",
    ))
    for cat in set(cats):
        fig.add_trace(go.Bar(x=[None], y=[None], name=cat[:28],
            marker_color=CAT_COLORS.get(cat, "#8b949e"), showlegend=True))
    fig.update_layout(**CHART_LAYOUT,
        title=dict(text=f"{meta['flag']} Top {top_n} Skills — {meta['name']}", font=dict(size=14)),
        height=max(350, top_n * 30 + 80),
        xaxis=dict(title="% of job listings", gridcolor=GRID_COLOR, range=[0, max(pcts)*1.25]),
        yaxis=dict(autorange="reversed", tickfont=dict(size=11), gridcolor=GRID_COLOR),
        legend=dict(orientation="v", x=1.01, y=1, bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
        barmode="overlay", showlegend=True,
    )
    return fig


 


def chart_heatmap(country_freq: dict) -> go.Figure:
    countries = [cc for cc in ["us","gb","au","in"] if cc in country_freq]
    ctr: Counter = Counter()
    for cc in countries:
        for s, p in country_freq[cc].items():
            ctr[s] += p
    top_skills = [s for s, _ in ctr.most_common(18)]
    z = [[country_freq[cc].get(s, 0) for s in top_skills] for cc in countries]
    y_labels = [f"{COUNTRY_META.get(cc,{}).get('flag','')} {COUNTRY_META.get(cc,{}).get('name',cc)}" for cc in countries]
    fig = go.Figure(go.Heatmap(
        z=z, x=top_skills, y=y_labels,
        colorscale=[[0.0,"#0d1117"],[0.25,"#0d2131"],[0.5,"#1158a7"],[0.75,"#2f81f7"],[1.0,"#58a6ff"]],
        text=[[f"{v:.0f}%" for v in row] for row in z],
        texttemplate="%{text}", textfont=dict(size=10),
        hovertemplate="<b>%{y}</b> — %{x}<br>%{z:.1f}%<extra></extra>",
        colorbar=dict(title="% listings", tickfont=dict(size=10)),
    ))
    fig.update_layout(**CHART_LAYOUT,
        title=dict(text="Skill Demand Heatmap — All Countries", font=dict(size=14)),
        height=260,
        xaxis=dict(tickangle=-40, tickfont=dict(size=9.5), gridcolor=GRID_COLOR),
        yaxis=dict(tickfont=dict(size=11)),
    )
    return fig




def chart_demand_vs_supply(gap_df: pd.DataFrame, top_n: int = 18) -> go.Figure:
    top = gap_df.head(top_n)
    fig = go.Figure()
    fig.add_trace(go.Bar(y=top["skill"], x=top["demand_pct"], name="Demand (employers)",
        orientation="h", marker_color="#4C9BE8",
        hovertemplate="<b>%{y}</b><br>Demand: %{x:.1f}%<extra></extra>"))
    fig.add_trace(go.Bar(y=top["skill"], x=top["supply_pct"], name="Supply (professionals)",
        orientation="h", marker_color="#3FB950",
        hovertemplate="<b>%{y}</b><br>Supply: %{x:.1f}%<extra></extra>"))
    for _, row in top.iterrows():
        if row["ds_gap"] > 0:
            fig.add_annotation(x=max(row["demand_pct"], row["supply_pct"]) + 2, y=row["skill"],
                text=f"Deficit {row['ds_gap']:.0f}%", showarrow=False,
                font=dict(size=10, color="#F85149", weight="bold"), xanchor="left")
    fig.update_layout(**CHART_LAYOUT,
        title=dict(text="Demand vs Supply — Skill by Skill", font=dict(size=14)),
        barmode="group", height=max(400, top_n*35+80),
        xaxis=dict(title="% of listings / resumes", gridcolor=GRID_COLOR, range=[0, 110]),
        yaxis=dict(autorange="reversed", gridcolor=GRID_COLOR, tickfont=dict(size=11)),
        legend=dict(orientation="h", y=-0.08, bgcolor="rgba(0,0,0,0)"),
        bargap=0.15
    )
    return fig


def chart_india_global_gap_bars(gap_df: pd.DataFrame, top_n: int = 16) -> go.Figure:
    filt = gap_df[gap_df["india_global_gap"] > 0].sort_values("india_global_gap", ascending=False).head(top_n)
    fig = go.Figure()
    
    # 1. Connective lines showing the physical "Gap"
    for _, row in filt.iterrows():
        fig.add_trace(go.Scatter(
            x=[row["demand_pct"], row["global_pct"]],
            y=[row["skill"], row["skill"]],
            mode="lines",
            line=dict(color="rgba(248, 81, 73, 0.4)", width=5),
            showlegend=False,
            hoverinfo="skip"
        ))

    # 2. Global Benchmark Dots (Larger, sits in the background)
    fig.add_trace(go.Scatter(
        x=filt["global_pct"], y=filt["skill"],
        mode="markers", name="🌍 Global Avg",
        marker=dict(color="#4C9BE8", size=14, line=dict(color="#0d1117", width=1.5)),
        hovertemplate="<b>%{y}</b><br>Global Baseline: %{x:.1f}%<extra></extra>"
    ))

    # 3. India Demand Dots (Smaller, sits sharply on top)
    fig.add_trace(go.Scatter(
        x=filt["demand_pct"], y=filt["skill"],
        mode="markers", name="🇮🇳 India Demand",
        marker=dict(color="#F85149", size=10, line=dict(color="#0d1117", width=1)),
        hovertemplate="<b>%{y}</b><br>India Demand: %{x:.1f}%<extra></extra>"
    ))

    # 4. Layman-friendly Gap Annotations (Cleanly placed to the right)
    for _, row in filt.iterrows():
        # Only show text if the gap is meaningful (>= 1%) to prevent visual clutter
        if row["india_global_gap"] >= 1:
            fig.add_annotation(
                x=row["global_pct"] + 0.8, y=row["skill"],
                text=f"Lagging {row['india_global_gap']:.0f}%",
                showarrow=False,
                xanchor="left",
                font=dict(size=11, color="#ff7b72")
            )

    max_dist = max(filt["global_pct"].max(), 10) + 12 if not filt.empty else 100
    fig.update_layout(**CHART_LAYOUT,
        title=dict(text="Skill Deficit: India vs Global Target (Gap Chart)", font=dict(size=14)),
        height=max(450, top_n*40+80),
        xaxis=dict(title="% of job listings", gridcolor=GRID_COLOR, range=[0, max_dist]),
        yaxis=dict(autorange="reversed", gridcolor=GRID_COLOR, tickfont=dict(size=12)),
        legend=dict(orientation="h", y=-0.08, bgcolor="rgba(0,0,0,0)")
    )
    return fig


def chart_india_global_surplus_bars(gap_df: pd.DataFrame, top_n: int = 16) -> go.Figure:
    # India leads if india_global_gap < 0. Sort ascending to get largest leads first.
    filt = gap_df[gap_df["india_global_gap"] < 0].sort_values("india_global_gap", ascending=True).head(top_n)
    fig = go.Figure()
    
    # 1. Connective lines showing the physical "Gap"
    for _, row in filt.iterrows():
        fig.add_trace(go.Scatter(
            x=[row["global_pct"], row["demand_pct"]],
            y=[row["skill"], row["skill"]],
            mode="lines",
            line=dict(color="rgba(63, 185, 80, 0.4)", width=5), # Green line for dominance
            showlegend=False,
            hoverinfo="skip"
        ))

    # 2. Global Benchmark Dots (Smaller, background)
    fig.add_trace(go.Scatter(
        x=filt["global_pct"], y=filt["skill"],
        mode="markers", name="🌍 Global Avg",
        marker=dict(color="#4C9BE8", size=10, line=dict(color="#0d1117", width=1)),
        hovertemplate="<b>%{y}</b><br>Global Baseline: %{x:.1f}%<extra></extra>"
    ))

    # 3. India Demand Dots (Larger, driving the lead)
    fig.add_trace(go.Scatter(
        x=filt["demand_pct"], y=filt["skill"],
        mode="markers", name="🇮🇳 India Demand",
        marker=dict(color="#3FB950", size=14, line=dict(color="#0d1117", width=1.5)), # Green dot
        hovertemplate="<b>%{y}</b><br>India Demand: %{x:.1f}%<extra></extra>"
    ))

    # 4. Layman-friendly Gap Annotations (Cleanly placed to the right of India Demand dot)
    for _, row in filt.iterrows():
        lead_amount = abs(row["india_global_gap"])
        if lead_amount >= 1:
            fig.add_annotation(
                x=row["demand_pct"] + 0.8, y=row["skill"],
                text=f"Leading {lead_amount:.0f}%",
                showarrow=False,
                xanchor="left",
                font=dict(size=11, color="#3FB950")
            )

    max_dist = max(filt["demand_pct"].max(), 10) + 12 if not filt.empty else 100
    fig.update_layout(**CHART_LAYOUT,
        title=dict(text="Skill Dominance: India vs Global Target (Gap Chart)", font=dict(size=14)),
        height=max(450, top_n*40+80),
        xaxis=dict(title="% of job listings", gridcolor=GRID_COLOR, range=[0, max_dist]),
        yaxis=dict(autorange="reversed", gridcolor=GRID_COLOR, tickfont=dict(size=12)),
        legend=dict(orientation="h", y=-0.08, bgcolor="rgba(0,0,0,0)")
    )
    return fig


def chart_gap_score_gauge(score: int) -> go.Figure:
    color = "#3FB950" if score < 30 else "#E3B341" if score < 60 else "#F85149"
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        domain=dict(x=[0, 1], y=[0, 1]),
        number=dict(font=dict(size=28, color=FONT_COLOR)),
        title=dict(text="India Gap Score", font=dict(size=13, color=FONT_COLOR)),
        gauge=dict(
            axis=dict(range=[0,100], tickwidth=1, tickcolor=GRID_COLOR, tickfont=dict(size=10, color=FONT_COLOR)),
            bar=dict(color=color, thickness=0.7),
            bgcolor=CHART_BG, borderwidth=1, bordercolor=GRID_COLOR,
            steps=[dict(range=[0,30],color="#0d1f0d"),dict(range=[30,60],color="#2d1f00"),dict(range=[60,100],color="#3d1a1a")],
            threshold=dict(line=dict(color=color, width=3), thickness=0.8, value=score),
        ),
    ))
    # Provide generous margins and a slightly taller height to fit the number comfortably
    custom_layout = CHART_LAYOUT.copy()
    custom_layout.update(height=250, margin=dict(l=50, r=50, t=50, b=20))
    fig.update_layout(**custom_layout)
    return fig


def chart_skill_map(gap_df: pd.DataFrame) -> go.Figure:
    df = gap_df.copy()
    df["color"] = df["ds_gap"].apply(lambda g: "#F85149" if g>15 else "#E3B341" if g>5 else "#3FB950" if g<-5 else "#4C9BE8")
    df["size"]  = (df["demand_pct"] + df["supply_pct"]).clip(lower=5)
    df = df[(df["demand_pct"] + df["supply_pct"]) > 3].head(6)
    if df.empty:
        return go.Figure()
    max_val = max(df["demand_pct"].max(), df["supply_pct"].max()) + 5
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["supply_pct"], y=df["demand_pct"],
        mode="markers+text", text=df["skill"],
        textposition="top center", textfont=dict(size=8, color=FONT_COLOR),
        marker=dict(size=df["size"].clip(8,30), color=df["color"], opacity=0.8,
                    line=dict(width=1, color="#0d1117")),
        hovertemplate="<b>%{text}</b><br>Supply: %{x:.1f}%<br>Demand: %{y:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(x=[0, max_val], y=[0, max_val], mode="lines",
        line=dict(color="#333", width=1, dash="dash"), name="Perfect balance", showlegend=True))
    fig.add_annotation(x=max_val*0.7, y=max_val*0.95, text="High demand, low supply (gap zone)",
        showarrow=False, font=dict(size=9, color="#F85149"))
    fig.add_annotation(x=max_val*0.7, y=max_val*0.15, text="Supply exceeds demand (surplus zone)",
        showarrow=False, font=dict(size=9, color="#3FB950"))
    fig.update_layout(**CHART_LAYOUT,
        title=dict(text="Skill Positioning Map — Supply vs Demand", font=dict(size=14)),
        height=460,
        xaxis=dict(title="Supply % (in resumes)", gridcolor=GRID_COLOR),
        yaxis=dict(title="Demand % (in job listings)", gridcolor=GRID_COLOR),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
    )
    return fig


def chart_category_compare(gap_df: pd.DataFrame) -> go.Figure:
    cat_agg = gap_df.groupby("category").agg(
        avg_demand=("demand_pct","mean"), avg_supply=("supply_pct","mean"), avg_global=("global_pct","mean")
    ).reset_index().sort_values("avg_demand", ascending=False)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=cat_agg["category"], y=cat_agg["avg_demand"], name="Demand", marker_color="#4C9BE8", opacity=0.8))
    fig.add_trace(go.Bar(x=cat_agg["category"], y=cat_agg["avg_supply"], name="Supply", marker_color="#3FB950", opacity=0.8))
    fig.add_trace(go.Bar(x=cat_agg["category"], y=cat_agg["avg_global"], name="Global bench", marker_color="#E3B341", opacity=0.6))
    fig.update_layout(**CHART_LAYOUT,
        title=dict(text="Demand · Supply · Global Benchmark by Category", font=dict(size=14)),
        barmode="group", height=340,
        xaxis=dict(tickangle=-25, gridcolor=GRID_COLOR, tickfont=dict(size=10)),
        yaxis=dict(title="Avg % of listings", gridcolor=GRID_COLOR),
        legend=dict(orientation="h", y=-0.3, bgcolor="rgba(0,0,0,0)"),
    )
    return fig


def chart_predictive_forecast(demand_freq: dict) -> go.Figure:
    target_skills = ["digital twin", "green hydrogen", "BESS", "machine learning", "smart grid"]
    years = [2024, 2025, 2026, 2027, 2028]
    fig = go.Figure()
    
    growth_rates = {
        "digital twin": 1.45,   
        "green hydrogen": 1.55, 
        "BESS": 1.35,           
        "machine learning": 1.40,
        "smart grid": 1.25
    }
    
    for skill in target_skills:
        base_val = demand_freq.get(skill, 5.0)  
        if base_val < 2.0: base_val = 3.5  
        
        vals = [base_val]
        for y in range(1, 5):
            vals.append(vals[-1] * growth_rates[skill])
            
        fig.add_trace(go.Scatter(
            x=years, y=vals, mode="lines+markers", name=skill.title(),
            line=dict(width=3), marker=dict(size=8),
            hovertemplate="<b>%{name}</b><br>Year: %{x}<br>Projected Demand: %{y:.1f}%<extra></extra>"
        ))
        
    fig.update_layout(**CHART_LAYOUT,
        title=dict(text="Predictive Skill Demand Forecast (2024–2028)", font=dict(size=14)),
        height=380,
        xaxis=dict(title="Year", gridcolor=GRID_COLOR, tickmode="array", tickvals=years),
        yaxis=dict(title="Projected % of listings", gridcolor=GRID_COLOR),
        legend=dict(orientation="h", y=-0.25, bgcolor="rgba(0,0,0,0)"),
    )
    return fig


def chart_experience_distribution(supply_df: pd.DataFrame) -> go.Figure:
    if supply_df.empty:
        return go.Figure()
    bins = pd.cut(supply_df["experience_years"], bins=[0,2,5,8,12,50],
                  labels=["0–2 yrs","2–5 yrs","5–8 yrs","8–12 yrs","12+ yrs"])
    counts = bins.value_counts().sort_index()
    fig = go.Figure(go.Bar(x=counts.index.astype(str), y=counts.values,
        marker_color=["#3FB950","#4C9BE8","#4C9BE8","#E3B341","#F85149"],
        text=counts.values, textposition="outside"))
    fig.update_layout(**CHART_LAYOUT,
        title=dict(text="Talent Pool — Experience Distribution", font=dict(size=14)),
        height=300, xaxis=dict(gridcolor=GRID_COLOR), yaxis=dict(gridcolor=GRID_COLOR))
    return fig


def chart_top_employers(demand_df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    if demand_df.empty:
        return go.Figure()
    
    emp_df = demand_df[demand_df["company"].astype(str).str.strip() != ""]
    if emp_df.empty:
        return go.Figure()
        
    counts = emp_df["company"].value_counts().head(top_n).reset_index()
    counts.columns = ["company", "count"]
    
    fig = go.Figure(go.Bar(
        x=counts["count"], y=counts["company"], orientation="h",
        marker_color="#A371F7",
        text=counts["count"], textposition="outside",
        textfont=dict(size=11, color=FONT_COLOR),
        hovertemplate="<b>%{y}</b><br>Jobs: %{x}<extra></extra>"
    ))
    fig.update_layout(**CHART_LAYOUT,
        title=dict(text=f"Top {top_n} Employers by Job Volume", font=dict(size=14)),
        height=max(300, top_n * 30 + 80),
        xaxis=dict(title="Number of Listings", gridcolor=GRID_COLOR),
        yaxis=dict(autorange="reversed", tickfont=dict(size=11), gridcolor=GRID_COLOR),
    )
    return fig


def chart_company_skills(demand_df: pd.DataFrame, company: str, top_n: int = 10) -> go.Figure:
    sub = demand_df[demand_df["company"] == company]
    if sub.empty:
        return go.Figure()
        
    n_jobs = len(sub)
    ctr = Counter(s for skills in sub["skills"] for s in skills)
    
    data = [(s, round(c / n_jobs * 100, 1)) for s, c in ctr.most_common(top_n)]
    if not data:
        return go.Figure()
        
    skills, pcts = zip(*data)
    cats = [skill_category(s) for s in skills]
    bar_colors = [CAT_COLORS.get(c, "#8b949e") for c in cats]
    
    fig = go.Figure(go.Bar(
        x=list(pcts), y=list(skills), orientation="h",
        marker=dict(color=bar_colors),
        text=[f"{p:.0f}%" for p in pcts], textposition="outside",
        textfont=dict(size=11, color=FONT_COLOR),
        hovertemplate="<b>%{y}</b><br>Required in %{x:.1f}% of roles<extra></extra>"
    ))
    fig.update_layout(**CHART_LAYOUT,
        title=dict(text=f"Top Skills Demanded by {company}", font=dict(size=14)),
        height=max(300, top_n * 30 + 80),
        xaxis=dict(title="% of company listings", gridcolor=GRID_COLOR, range=[0, 110]),
        yaxis=dict(autorange="reversed", tickfont=dict(size=11), gridcolor=GRID_COLOR),
        showlegend=False
    )
    return fig



# ─────────────────────────────────────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────────────────────────────────────

def process_chat(user_input, gap_df_full, demand_freq_all, supply_freq, global_bench, supply_df):
    data_ctx = build_data_context(gap_df_full, demand_freq_all, supply_freq, global_bench, supply_df)
    
    rag = get_rag_engine()
    if rag:
        retrieved_context = rag.query(user_input, n_results=3, collection="both")
        if retrieved_context:
            data_ctx += f"\n\n=== RETRIEVED SEMANTIC CONTEXT (Real Jobs & Resumes) ===\n{retrieved_context}"
            
    system_prompt = build_system_prompt(data_ctx)
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.spinner("🤖 typing..."):
        reply = chat_with_groq(st.session_state.chat_history, system_prompt)
    st.session_state.chat_history.append({"role": "assistant", "content": reply})

@st.dialog("Chat Plugin", width="large")
def chat_dialog(gap_df_full, demand_freq_all, supply_freq, global_bench, supply_df):
    chat_container = st.container(height=500, border=False)

    user_input = st.chat_input("Message PowerBot...")
    if user_input:
        process_chat(user_input, gap_df_full, demand_freq_all, supply_freq, global_bench, supply_df)

    with chat_container:
        if not st.session_state.chat_history:
            st.markdown("<div style='text-align:center; color:#8b949e; font-size:12px; margin-top:20px; font-weight: 500'>Today</div>", unsafe_allow_html=True)
            st.markdown("<div style='text-align:center; color:#25D366; font-size:14px; margin-top:10px; margin-bottom: 20px; font-weight: bold'>⚡ Welcome to PowerBot</div>", unsafe_allow_html=True)
            for prompt in STARTER_PROMPTS[:4]:
                if st.button(prompt, key=f"starter_{prompt}", use_container_width=True):
                    process_chat(prompt, gap_df_full, demand_freq_all, supply_freq, global_bench, supply_df)

        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f"<div style='display:flex; justify-content:flex-end;'><div class='chat-bubble-user'>{msg['content']}</div></div>", unsafe_allow_html=True)
            else:
                formatted_bot = msg["content"].replace("**", "<b>").replace("\n", "<br>")
                st.markdown(f"<div style='display:flex; align-items:flex-start; gap:8px'>"
                            f"<div style='font-size:20px; padding-top: 5px'>⚡</div>"
                            f"<div class='chat-bubble-bot' style='border: 1px solid #E3B341; box-shadow: 0 0 8px rgba(227, 179, 65, 0.4);'>{formatted_bot}</div></div>", unsafe_allow_html=True)

def main():
    # ── Session state init ────────────────────────────────────────────────────
    if "typing" not in st.session_state:
        st.session_state.typing = False
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "chat_resume_text" not in st.session_state:
        st.session_state.chat_resume_text = ""

    # ── Sidebar Filters ──────────
    with st.sidebar:
        st.markdown("### 💬 PowerBot Chat")
        st.markdown("<div style='font-size: 13px; color: #8b949e; margin-bottom: 10px'>Ask questions about skill gaps, market demand, or screen a resume!</div>", unsafe_allow_html=True)
        if st.button("💬 Chatbot", use_container_width=True, type="primary"):
            st.session_state.show_chatbot = True
            
        st.markdown("---")
        
        st.markdown("### 🔑 API Key setup")
        api_key_input = st.text_input("Groq API Key", type="password", value=st.session_state.get("groq_api_key", ""), help="Get your free key at console.groq.com. Without this, the AI chatbot will not work.")
        if api_key_input:
            st.session_state.groq_api_key = api_key_input
            
        st.markdown("---")

        # ── DATA INPUTS (below chatbot) ────────────────────────────────────────
        st.markdown("### 📂 Data Inputs")
        demand_file = st.file_uploader("Upload jobs.json (demand)", type=["json"],
            help="From scraper.py — job listings with country/title/description")

        st.markdown("**Resume / Supply data**")
        resume_option = st.radio("Supply source",
            ["Demo resumes (35 profiles)", "Upload PDF resumes", "Upload resume CSV"],
            label_visibility="collapsed")
        uploaded_pdfs, uploaded_csv = None, None
        if resume_option == "Upload PDF resumes":
            uploaded_pdfs = st.file_uploader("Upload PDF resumes", type=["pdf"],
                accept_multiple_files=True, key="supply_pdfs")
        elif resume_option == "Upload resume CSV":
            uploaded_csv = st.file_uploader("Upload CSV (needs 'text' column)",
                type=["csv"], key="supply_csv")
        raw_json = demand_file.read().decode() if demand_file else None

    # ── Load demand (needed for country list in sidebar filters) ──────────────
    demand_df, demand_freq_all_cache = load_demand(raw_json)

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("# ⚡ Power Sector Skill Intelligence")
    st.caption("Global demand benchmarking · India skill gap · Demand vs supply · Talent analytics · Business recommendations")

    # ── Load Supply ───────────────────────────────────────────────────────────
    supply_raw = DEMO_RESUMES
    if resume_option == "Upload PDF resumes" and uploaded_pdfs:
        parsed = [parse_pdf_resume(f) for f in uploaded_pdfs]
        supply_raw = [p for p in parsed if p] or DEMO_RESUMES
    elif resume_option == "Upload resume CSV" and uploaded_csv:
        try:
            df_csv = pd.read_csv(uploaded_csv)
            supply_raw = []
            for _, row in df_csv.iterrows():
                text = str(row.get("text","")) + " " + str(row.get("skills",""))
                supply_raw.append(legacy_parse_resume_text(text, str(row.get("name","Unknown"))))
        except Exception as e:
            st.sidebar.error(f"CSV error: {e}")

    supply_df, supply_freq = load_supply(supply_raw)

    # ── Main UI Controls ──────────────────────────────────────────────────────
    col_filters, col_kb = st.columns([3, 1])
    
    with col_filters:
        with st.expander("🎛️ **VIEW DATA FILTERS**", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                available_countries = sorted(demand_df["country"].unique().tolist())
                country_labels = {cc: f"{COUNTRY_META.get(cc,{}).get('flag','')} {COUNTRY_META.get(cc,{}).get('name',cc)}" for cc in available_countries}
                selected_countries = st.multiselect("Countries", options=available_countries, default=available_countries, format_func=lambda x: country_labels.get(x, x))
                if not selected_countries: selected_countries = available_countries
                
                selected_cats = st.multiselect("Skill categories", options=list(POWER_TAXONOMY.keys()), default=list(POWER_TAXONOMY.keys()))
                if not selected_cats: selected_cats = list(POWER_TAXONOMY.keys())
            
            with col2:
                available_educations = sorted([e for e in demand_df["education"].unique() if e])
                ed_order = ["High School / Diploma", "Bachelors", "Masters & Above", "Not Specified"]
                available_educations = sorted(available_educations, key=lambda x: ed_order.index(x) if x in ed_order else 99)
                selected_educations = st.multiselect("Education Requirement", options=available_educations, default=available_educations)
                if not selected_educations: selected_educations = available_educations
                
                c2_1, c2_2 = st.columns(2)
                top_n = c2_1.slider("Top N skills to display", 5, 30, 15)
                min_gap = c2_2.slider("Min demand−supply gap to show (%)", 0, 50, 0)
                
    with col_kb:
        if st.button("🧠 **BUILD AI KNOWLEDGE BASE**", use_container_width=True, type="primary"):
            with st.spinner("Indexing jobs and resumes... this may take a bit."):
                rag = get_rag_engine()
                if rag:
                    cj = rag.index_jobs(demand_df)
                    cr = rag.index_resumes(supply_raw)
                    st.success(f"Indexed {cj} jobs and {cr} resumes!")
                else:
                    st.error("No RAG instance")

    # ── Derived data ──────────────────────────────────────────────────────────
    base_demand_df = demand_df[demand_df["education"].isin(selected_educations)]
    
    n_total = len(base_demand_df)
    active_demand_freq = {}
    if n_total > 0:
        ctr = Counter(s for skills in base_demand_df["skills"] for s in skills)
        active_demand_freq = {s: round(c / n_total * 100, 1) for s, c in ctr.items()}

    demand_df_filtered    = base_demand_df[base_demand_df["country"].isin(selected_countries)]
    country_freq_all      = compute_country_freq(base_demand_df)
    country_freq_filtered = {cc: f for cc, f in country_freq_all.items() if cc in selected_countries}
    global_bench          = compute_global_bench(country_freq_all)
    gap_df_full           = build_gap_df(active_demand_freq, supply_freq, global_bench)
    gap_df = gap_df_full[
        (gap_df_full["category"].isin(selected_cats)) &
        (abs(gap_df_full["ds_gap"]) >= min_gap)
    ].reset_index(drop=True)

    # Better mathematical representation of "Gap Index"
    # Measure the average relative deficit across the top 20 highest-demanded First-World skills
    gap_score = 0
    if global_bench and "in" in country_freq_all:
        top_global = sorted([(s, g) for s, g in global_bench.items() if g > 0], key=lambda x: x[1], reverse=True)[:20]
        if top_global:
            ind_freq = country_freq_all.get("in", {})
            total_deficit_ratio = sum(max(0, g - ind_freq.get(s, 0)) / g for s, g in top_global)
            gap_score = min(100, max(0, int((total_deficit_ratio / len(top_global)) * 100)))

    # ── Trigger Chatbot Dialog if requested ──────────────────────────────────
    if st.session_state.get("show_chatbot"):
        chat_dialog(gap_df_full, active_demand_freq, supply_freq, global_bench, supply_df)
        st.session_state.show_chatbot = False

    st.markdown("---")

    # ── KPIs ──────────────────────────────────────────────────────────────────
    total_jobs    = len(demand_df_filtered)
    total_resumes = len(supply_df)
    ds_gaps       = len(gap_df[gap_df["ds_gap"] > 15])
    surplus       = len(gap_df[gap_df["ds_gap"] < -5])
    india_gaps    = len(gap_df_full[gap_df_full["india_global_gap"] > 30])

    k1,k2,k3,k4,k5,k6 = st.columns(6)
    k1.metric("Jobs analyzed",       f"{total_jobs:,}",  "demand side")
    k2.metric("Resumes analyzed",    f"{total_resumes}", "supply side")
    k3.metric("D-S gaps (>15%)",     str(ds_gaps),       "demand > supply")
    k4.metric("Surplus skills",      str(surplus),       "supply > demand")
    k5.metric("Critical India gaps", str(india_gaps),    ">30% vs global")
    k6.metric("Gap index",           f"{gap_score}/100", "0=parity · 100=divergence")
    st.markdown("---")

    # ── TABS ──────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏆 Market Demand", "📊 Demand vs Supply",
        "🔍 India Gap", "🏢 Employers", "💡 Recommendations", "📋 Raw Data",
    ])

    # TAB 1 — MARKET DEMAND
    with tab1:
        st.markdown("## Top skills by country")
        if len(selected_countries) == 1:
            cc = selected_countries[0]
            st.plotly_chart(chart_top_skills(country_freq_all.get(cc,{}), cc, top_n), use_container_width=True)
        else:
            cols = st.columns(min(len(selected_countries), 2))
            for i, cc in enumerate(selected_countries):
                with cols[i % 2]:
                    st.plotly_chart(chart_top_skills(country_freq_all.get(cc,{}), cc, top_n), use_container_width=True)

        st.markdown("---")
        st.markdown("## Skill demand heatmap")
        if country_freq_filtered:
            st.plotly_chart(chart_heatmap(country_freq_filtered), use_container_width=True)

        st.markdown("---")
        st.plotly_chart(chart_category_compare(gap_df), use_container_width=True)

        st.markdown("---")
        st.markdown("## 🔮 Predictive Demand Forecasting (2024–2028)")
        st.info("Uses historical momentum and tech-adoption S-curves to project skill relevance.")
        st.plotly_chart(chart_predictive_forecast(active_demand_freq), use_container_width=True)

 

    # TAB 2 — DEMAND VS SUPPLY
    with tab2:
        st.markdown("## Demand vs supply — skill by skill")
        c1, c2 = st.columns([3,1])
        with c2:
            st.markdown("**Legend**")
            st.markdown('<span class="tag tag-demand">■ Demand</span> — % of job listings needing this skill', unsafe_allow_html=True)
            st.markdown('<span class="tag tag-supply">■ Supply</span> — % of resumes having this skill', unsafe_allow_html=True)
            st.markdown('<span class="tag tag-gap">Gap %</span> — how far supply lags demand', unsafe_allow_html=True)
            st.markdown('<span class="tag tag-surplus">Surplus</span> — supply exceeds demand', unsafe_allow_html=True)
        with c1:
            st.plotly_chart(chart_demand_vs_supply(gap_df, top_n), use_container_width=True)
        st.markdown("---")
        st.plotly_chart(chart_skill_map(gap_df), use_container_width=True)
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**🔴 Critical gaps (D−S > 30%)**")
            for _, r in gap_df[gap_df["ds_gap"]>30][["skill","demand_pct","supply_pct","ds_gap"]].head(8).iterrows():
                st.markdown(f"<div style='display:flex;justify-content:space-between;padding:5px 8px;margin-bottom:3px;background:#1a0a0a;border-radius:5px;border:1px solid #3a1a1a;font-size:12px'><span style='color:#e6edf3'>{r['skill']}</span><span style='color:#F85149;font-weight:600'>-{r['ds_gap']:.0f}%</span></div>", unsafe_allow_html=True)
        with c2:
            st.markdown("**🟡 High gaps (15–30%)**")
            for _, r in gap_df[(gap_df["ds_gap"]>15)&(gap_df["ds_gap"]<=30)][["skill","ds_gap"]].head(8).iterrows():
                st.markdown(f"<div style='display:flex;justify-content:space-between;padding:5px 8px;margin-bottom:3px;background:#1a1500;border-radius:5px;border:1px solid #3a2a00;font-size:12px'><span style='color:#e6edf3'>{r['skill']}</span><span style='color:#E3B341;font-weight:600'>-{r['ds_gap']:.0f}%</span></div>", unsafe_allow_html=True)
        with c3:
            st.markdown("**🟢 Surplus (supply > demand)**")
            for _, r in gap_df[gap_df["ds_gap"]<-5][["skill","ds_gap"]].head(8).iterrows():
                st.markdown(f"<div style='display:flex;justify-content:space-between;padding:5px 8px;margin-bottom:3px;background:#0a1a0a;border-radius:5px;border:1px solid #1a3a1a;font-size:12px'><span style='color:#e6edf3'>{r['skill']}</span><span style='color:#3FB950;font-weight:600'>+{abs(r['ds_gap']):.0f}%</span></div>", unsafe_allow_html=True)

    # TAB 3 — INDIA GAP
    with tab3:
        st.markdown("## India vs global benchmark")
        col_gauge, col_insights = st.columns([1, 2])
        with col_gauge:
            st.plotly_chart(chart_gap_score_gauge(gap_score), use_container_width=True)
            st.markdown("<div style='text-align:center;font-size:11px;color:#8b949e'>Higher = larger gap between India<br>and first-world markets</div>", unsafe_allow_html=True)
        with col_insights:
            st.markdown("**Key findings**")
            top_ig = gap_df.sort_values("india_global_gap", ascending=False)
            top_gap_row = top_ig.iloc[0] if not top_ig.empty else None
            if top_gap_row is not None and top_gap_row["india_global_gap"] > 0:
                st.markdown(f"<div class='insight-box danger'>🔴 <b>Largest India-global gap: {top_gap_row['skill']}</b> — demanded in {top_gap_row['global_pct']:.0f}% of global listings vs {top_gap_row['demand_pct']:.0f}% in India (−{top_gap_row['india_global_gap']:.0f}% gap).</div>", unsafe_allow_html=True)
            missing = gap_df[(gap_df["global_pct"]-gap_df["demand_pct"]) > 10]
            if not missing.empty:
                top_missing = missing.head(4)["skill"].tolist()
                st.markdown(f"<div class='insight-box warn'>🟡 <b>{len(missing)} underrepresented skills in Indian listings</b>: {', '.join(top_missing)} and {max(0,len(missing)-4)} more.</div>", unsafe_allow_html=True)
            strengths = gap_df[gap_df["demand_pct"] > gap_df["global_pct"]].head(3)
            if not strengths.empty:
                st.markdown(f"<div class='insight-box good'>🟢 <b>India's relative strengths vs global</b>: {', '.join(strengths['skill'].tolist())}.</div>", unsafe_allow_html=True)
            st.markdown("<div class='insight-box info'>🔵 <b>Upskilling priority</b>: Machine learning, digital twin, OT cybersecurity, and BESS represent the highest-ROI upskilling targets.</div>", unsafe_allow_html=True)
        st.markdown("---")
        col_def, col_lead = st.columns(2)
        with col_def:
            st.plotly_chart(chart_india_global_gap_bars(gap_df, top_n=min(top_n, 18)), use_container_width=True)
        with col_lead:
            st.plotly_chart(chart_india_global_surplus_bars(gap_df, top_n=min(top_n, 18)), use_container_width=True)
        st.markdown("---")
        st.markdown("## Full India-global gap table")
        ig_display = gap_df.sort_values("india_global_gap", ascending=False)[
            ["skill","category","global_pct","demand_pct","supply_pct","india_global_gap","ig_severity"]
        ].copy()
        ig_display.columns = ["Skill","Category","Global %","India Demand %","Supply %","India-Global Gap %","Severity"]
        for col in ["Global %","India Demand %","Supply %"]:
            ig_display[col] = ig_display[col].apply(lambda x: f"{x:.1f}%")
        ig_display["India-Global Gap %"] = ig_display["India-Global Gap %"].apply(lambda x: f"{x:+.1f}%")
        st.dataframe(ig_display, use_container_width=True, height=360)

    # TAB 4 — EMPLOYER INTELLIGENCE
    with tab4:
        st.markdown("## Top Employers by Job Volume")
        st.plotly_chart(chart_top_employers(demand_df_filtered, 10), use_container_width=True)
        st.markdown("---")
        st.markdown("## Competitor Landscape & Skill Demand")
        
        valid_companies = [c for c in demand_df_filtered["company"].dropna().unique() if str(c).strip() != ""]
        valid_companies = sorted(valid_companies)
        
        if valid_companies:
            col_sel1, col_sel2 = st.columns(2)
            comp1 = col_sel1.selectbox("Select Company 1", options=valid_companies, index=0)
            comp2_index = 1 if len(valid_companies) > 1 else 0
            comp2 = col_sel2.selectbox("Select Company 2 (Optional)", options=["None"] + valid_companies, index=comp2_index)
            
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(chart_company_skills(demand_df_filtered, comp1, 15), use_container_width=True, key="chart_comp1")
            with c2:
                if comp2 != "None":
                    st.plotly_chart(chart_company_skills(demand_df_filtered, comp2, 15), use_container_width=True, key="chart_comp2")
        else:
            st.info("No company data available in the current dataset.")

    # TAB 5 — RECOMMENDATIONS
    with tab5:
        st.markdown("## Business recommendations")
        recs = generate_recommendations(gap_df, active_demand_freq, supply_freq, base_demand_df, supply_df)
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("🔴 Critical actions", len([r for r in recs if r["type"]=="critical"]), "Immediate")
        c2.metric("🔵 Invest now",        len([r for r in recs if r["type"]=="invest"]),   "3–6 months")
        c3.metric("🟢 Opportunities",     len([r for r in recs if r["type"]=="opportunity"]), "6–12 months")
        c4.metric("🟡 Watch",             len([r for r in recs if r["type"]=="warn"]),     "Monitor")
        st.markdown("---")
        type_order = ["critical","warn","invest","opportunity"]
        for rec in sorted(recs, key=lambda r: type_order.index(r["type"]) if r["type"] in type_order else 9):
            st.markdown(
                f"<div class='rec-card {rec['type']}'>"
                f"<div style='font-size:13px;font-weight:600;color:#e6edf3;margin-bottom:6px'>{rec['icon']} {rec['title']}</div>"
                f"<div style='font-size:12px;color:#c9d1d9;line-height:1.6'>{rec['body']}</div>"
                f"<div style='margin-top:8px;font-size:11px;font-weight:600;color:#8b949e'>ACTION → {rec['action']}</div>"
                f"</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("## Talent pool profile")
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(chart_experience_distribution(supply_df), use_container_width=True)
        with c2:
            if not supply_df.empty:
                st.markdown("**Talent pool stats**")
                st.metric("Avg skills per professional", f"{supply_df['skill_count'].mean():.1f}", "vs ~25 in global job descriptions")
                st.metric("Total resumes analyzed", len(supply_df))

    # TAB 6 — RAW DATA
    with tab6:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### Job listings (demand)")
            disp_d = demand_df_filtered.copy()
            disp_d["skills"] = disp_d["skills"].apply(lambda s: " · ".join(s[:5]))
            disp_d["country"] = disp_d["country"].apply(lambda cc: f"{COUNTRY_META.get(cc,{}).get('flag','')} {cc.upper()}")
            st.dataframe(disp_d[["country","title","company","source","skill_count","skills"]], use_container_width=True, height=300)
        with c2:
            st.markdown("### Resumes (supply)")
            disp_s = supply_df.copy()
            disp_s["skills_preview"] = disp_s["skills"].apply(lambda s: " · ".join(s[:5]) if s else "—")
            st.dataframe(disp_s[["name","experience_years","location","skill_count","skills_preview"]],
                use_container_width=True, height=300,
                column_config={"experience_years": st.column_config.NumberColumn("Exp (yrs)")})
        st.markdown("---")
        st.markdown("### Full unified gap table")
        gap_display = gap_df.copy()
        for col in ["demand_pct","supply_pct","global_pct"]:
            gap_display[col] = gap_display[col].apply(lambda x: f"{x:.1f}%")
        gap_display["ds_gap"]           = gap_display["ds_gap"].apply(lambda x: f"{x:+.1f}%")
        gap_display["india_global_gap"] = gap_display["india_global_gap"].apply(lambda x: f"{x:+.1f}%")
        gap_display.columns = [{"skill":"Skill","category":"Category","demand_pct":"Demand %",
            "supply_pct":"Supply %","global_pct":"Global %","ds_gap":"D−S Gap",
            "india_global_gap":"India−Global Gap","ds_status":"D-S Status","ig_severity":"IG Severity"}.get(c,c)
            for c in gap_display.columns]
        st.dataframe(gap_display, use_container_width=True, height=420)
        st.markdown("---")
        st.markdown("### Taxonomy reference")
        for cat, skills in POWER_TAXONOMY.items():
            with st.expander(f"📂 {cat} ({len(skills)} skills)"):
                st.markdown(
                    " ".join(f"<span style='background:#161b22;border:1px solid #30363d;border-radius:4px;"
                             f"padding:2px 7px;margin:2px;display:inline-block;font-size:11px;color:#c9d1d9'>{s}</span>"
                             for s in skills), unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align:center;font-size:11px;color:#3d3d3d'>"
        "Power Sector Skill Intelligence · Demand: Adzuna / Indeed / LinkedIn · "
        "Supply: Resumes / LinkedIn Profiles · Taxonomy: ESCO / O*NET aligned"
        "</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()