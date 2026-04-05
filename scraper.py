"""
Power Sector Job Scraper
===================================
Collects job listings from:
  1. Adzuna API  (US, UK, AU, IN) — structured JSON, no auth wall
  2. Indeed RSS  (US, UK, AU, IN) — public RSS feed, no key needed
  3. LinkedIn    (public job search HTML, BeautifulSoup)

Usage:
    python scraper.py                     # runs all sources, saves jobs.json + jobs.csv
    python scraper.py --source adzuna     # only Adzuna
    python scraper.py --source indeed     # only Indeed
    python scraper.py --country in us     # filter countries
    python scraper.py --country in us gb au # all countries

Requirements:
    pip install requests beautifulsoup4 pandas
"""

import argparse
import json
import time
import re
import csv
import sys
from datetime import datetime
from typing import Optional
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
# ── Config ──────────────────────────────────────────────────────────────────

ADZUNA_APP_ID  = "1fc61054"   
ADZUNA_APP_KEY = "c87ab82c73bc1fccba640aeed890e51d"

# ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
# ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")
COUNTRIES = {
    "us": {"name": "United States", "adzuna": "us",  "indeed": "www.indeed.com",    "linkedin": "us"},
    "gb": {"name": "United Kingdom","adzuna": "gb",  "indeed": "uk.indeed.com",     "linkedin": "uk"},
    "au": {"name": "Australia",     "adzuna": "au",  "indeed": "au.indeed.com",     "linkedin": "au"},
    "in": {"name": "India",         "adzuna": "in",  "indeed": "in.indeed.com",     "linkedin": "in"},
}

POWER_QUERIES = [
    "power engineer",
    "electrical engineer power systems",
    "renewable energy engineer",
    "grid engineer",
    "energy storage engineer",
    "substation engineer",
    "wind energy engineer",
    "solar energy engineer",
    "smart grid engineer",
    "transmission distribution engineer",
    "SCADA engineer power",
    "protection relay engineer",
    "power electronics engineer",
    "EPC power project manager",
    "energy transition engineer",
    "offshore wind engineer",
    "battery storage engineer",
    "OT cybersecurity power",
    "digital twin energy",
    "net zero power sector",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ── Skills Taxonomy ──────────────────────────────────────────────────────────

POWER_TAXONOMY = {
    "Traditional Power Engineering": [
        "power systems","electrical engineering","substation","transformer",
        "switchgear","protection relay","load flow","short circuit","power factor",
        "reactive power","HV","LV","MV","11kV","33kV","132kV","400kV","busbar",
        "circuit breaker","earthing","SCADA","DCS","PLC","HMI","IED","RTU",
        "metering","energy audit","grid","distribution","transmission","ETAP","PSS/E",
    ],
    "Renewables & Energy Transition": [
        "solar PV","wind energy","wind turbine","battery storage","BESS",
        "energy storage","lithium ion","offshore wind","onshore wind","rooftop solar",
        "hybrid energy","microgrid","VPP","virtual power plant","EV charging",
        "green hydrogen","electrolysis","fuel cell","tidal","geothermal","biomass",
    ],
    "Digital & Analytics": [
        "data analytics","machine learning","AI","artificial intelligence","IoT",
        "digital twin","predictive maintenance","big data","python","MATLAB",
        "power BI","Tableau","cloud","AWS","Azure","GCP","cybersecurity",
        "OT security","DERMS","energy management system","smart meter","AMI",
        "edge computing","blockchain","digital transformation",
    ],
    "Grid Modernization": [
        "smart grid","grid modernization","flexibility","demand response",
        "ancillary services","frequency regulation","voltage regulation",
        "grid stability","HVDC","FACTS","SVC","STATCOM","power electronics",
        "inverter","converter","wide area monitoring","PMU","synchrophasor",
    ],
    "Project & Commercial": [
        "project management","PMP","EPC","O&M","feasibility study",
        "financial modelling","PPA","tariff","regulatory","offtake","contract",
        "procurement","capex","opex","IRR","NPV","due diligence","asset management",
        "HSE","HSSE","LOTO","permits",
    ],
    "Sustainability & Policy": [
        "ESG","carbon footprint","net zero","decarbonization","sustainability",
        "GHG","emissions","carbon credit","CDP","climate risk","TCFD","policy",
        "regulatory compliance","RE100","SBTi","just transition","circular economy",
    ],
}

ALL_SKILLS = [s for skills in POWER_TAXONOMY.values() for s in skills]


def extract_skills(text: str) -> list[str]:
    if not text:
        return []
    lower = text.lower()
    return [s for s in ALL_SKILLS if s.lower() in lower]


def categorize_skill(skill: str) -> str:
    for cat, skills in POWER_TAXONOMY.items():
        if any(s.lower() == skill.lower() for s in skills):
            return cat
    return "Other"


# ── Source 1: Adzuna API ─────────────────────────────────────────────────────

def scrape_adzuna(countries: list[str], max_per_query: int = 10) -> list[dict]:
    jobs = []
    print("\n[Adzuna API]")

    for cc in countries:
        cfg = COUNTRIES[cc]
        ac = cfg["adzuna"]

        for query in POWER_QUERIES[:5]:
            for page in range(1, 4):

                url = (
                    f"https://api.adzuna.com/v1/api/jobs/{ac}/search/{page}"
                    f"?app_id={ADZUNA_APP_ID}&app_key={ADZUNA_APP_KEY}"
                    f"&results_per_page=10"
                    f"&what={requests.utils.quote(query)}"
                    f"&content-type=application/json"
                )

                try:
                    r = requests.get(url, timeout=15)
                    r.raise_for_status()
                    data = r.json()
                    results = data.get("results", [])

                    for j in results:
                        desc = j.get("description", "")
                        title = j.get("title", "")

                        jobs.append({
                            "source": "adzuna",
                            "country": cc,
                            "country_name": cfg["name"],
                            "title": title,
                            "company": j.get("company", {}).get("display_name", ""),
                            "location": j.get("location", {}).get("display_name", ""),
                            "salary_min": j.get("salary_min"),
                            "salary_max": j.get("salary_max"),
                            "description": desc,
                            "url": j.get("redirect_url", ""),
                            "posted": j.get("created", ""),
                            "skills": extract_skills(title + " " + desc),
                            "query": query,
                            "fetched_at": datetime.utcnow().isoformat(),
                        })

                    print(f"{cc.upper()} | '{query}' | Page {page} → {len(results)} jobs")
                    time.sleep(0.5)

                except Exception as e:
                    print(f"Adzuna ERROR: {e}")

    print(f"Total Adzuna jobs: {len(jobs)}")
    return jobs


# ── Source 2: Indeed RSS ─────────────────────────────────────────────────────

def scrape_indeed_rss(countries: list[str]) -> list[dict]:
    """
    Scrapes Indeed's public RSS feeds — no API key required.
    RSS endpoint: https://{domain}/rss?q={query}&l={location}
    """
    jobs = []
    print("\n[Indeed RSS]")

    for cc in countries:
        cfg = COUNTRIES[cc]
        domain = cfg["indeed"]
        for query in POWER_QUERIES[:3]:
            url = f"https://{domain}/rss?q={requests.utils.quote(query)}&sort=date"
            try:
                r = requests.get(url, headers=HEADERS, timeout=15)
                r.raise_for_status()
                soup = BeautifulSoup(r.content, "xml")
                items = soup.find_all("item")
                for item in items[:15]:
                    title = item.find("title")
                    title = title.text.strip() if title else ""
                    desc_tag = item.find("description")
                    desc = BeautifulSoup(desc_tag.text, "html.parser").get_text() if desc_tag else ""
                    link = item.find("link")
                    link = link.text.strip() if link else ""
                    pubdate = item.find("pubDate")
                    pubdate = pubdate.text.strip() if pubdate else ""
                    # Extract company from title (Indeed format: "Title - Company")
                    company = ""
                    if " - " in title:
                        parts = title.rsplit(" - ", 1)
                        title = parts[0].strip()
                        company = parts[1].strip()
                    jobs.append({
                        "source":       "indeed_rss",
                        "country":      cc,
                        "country_name": cfg["name"],
                        "title":        title,
                        "company":      company,
                        "location":     "",
                        "salary_min":   None,
                        "salary_max":   None,
                        "description":  desc,
                        "url":          link,
                        "posted":       pubdate,
                        "skills":       extract_skills(title + " " + desc),
                        "query":        query,
                        "fetched_at":   datetime.utcnow().isoformat(),
                    })
                print(f"  {cc.upper()} | '{query}' → {len(items[:15])} jobs")
                time.sleep(1.0)
            except requests.RequestException as e:
                print(f"  {cc.upper()} | '{query}' → ERROR: {e}")
            except Exception as e:
                print(f"  {cc.upper()} | '{query}' → PARSE ERROR: {e}")

    print(f"  Total: {len(jobs)} jobs from Indeed RSS")
    return jobs


# ── Source 3: LinkedIn Public Search ────────────────────────────────────────

def scrape_linkedin(countries: list[str]) -> list[dict]:
    """
    Scrapes LinkedIn's public job search pages.
    Note: LinkedIn aggressively rate-limits scrapers. Use with delays.
    For production, consider the LinkedIn Jobs API (requires partnership).
    """
    jobs = []
    print("\n[LinkedIn Public Search]")

    location_map = {
        "us": "United States",
        "gb": "United Kingdom",
        "au": "Australia",
        "in": "India",
    }

    for cc in countries:
        location = location_map.get(cc, "")
        cfg = COUNTRIES[cc]
        for query in POWER_QUERIES[:2]:
            url = (
                "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
                f"?keywords={requests.utils.quote(query)}"
                f"&location={requests.utils.quote(location)}"
                f"&start=0&count=10"
            )
            try:
                r = requests.get(url, headers=HEADERS, timeout=20)
                if r.status_code == 429:
                    print(f"  {cc.upper()} | Rate limited by LinkedIn — skipping")
                    break
                r.raise_for_status()
                soup = BeautifulSoup(r.text, "html.parser")
                cards = soup.find_all("li")
                count = 0
                for card in cards:
                    title_el = card.find("h3", class_=re.compile("base-search-card__title"))
                    company_el = card.find("h4", class_=re.compile("base-search-card__subtitle"))
                    location_el = card.find("span", class_=re.compile("job-search-card__location"))
                    link_el = card.find("a", class_=re.compile("base-card__full-link"))
                    if not title_el:
                        continue
                    title = title_el.get_text(strip=True)
                    company = company_el.get_text(strip=True) if company_el else ""
                    loc = location_el.get_text(strip=True) if location_el else ""
                    link = link_el.get("href", "") if link_el else ""
                    jobs.append({
                        "source":       "linkedin",
                        "country":      cc,
                        "country_name": cfg["name"],
                        "title":        title,
                        "company":      company,
                        "location":     loc,
                        "salary_min":   None,
                        "salary_max":   None,
                        "description":  title,  # LinkedIn cards don't expose full desc
                        "url":          link,
                        "posted":       "",
                        "skills":       extract_skills(title + " " + company),
                        "query":        query,
                        "fetched_at":   datetime.utcnow().isoformat(),
                    })
                    count += 1
                print(f"  {cc.upper()} | '{query}' → {count} jobs")
                time.sleep(3.0)  # Respect LinkedIn's rate limits
            except requests.RequestException as e:
                print(f"  {cc.upper()} | '{query}' → ERROR: {e}")
            except Exception as e:
                print(f"  {cc.upper()} | '{query}' → PARSE ERROR: {e}")

    print(f"  Total: {len(jobs)} jobs from LinkedIn")
    return jobs


# ── Deduplication ────────────────────────────────────────────────────────────

def deduplicate(jobs: list[dict]) -> list[dict]:
    """Remove duplicate listings by (title, company, country) fingerprint."""
    seen = set()
    unique = []
    for j in jobs:
        key = (
            j["title"].lower().strip()[:60],
            j["company"].lower().strip()[:40],
            j["country"],
        )
        if key not in seen:
            seen.add(key)
            unique.append(j)
    return unique


# ── Save ─────────────────────────────────────────────────────────────────────
import os

def save(jobs, path_prefix="jobs"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = f"{path_prefix}_{timestamp}.csv"
    json_path = f"{path_prefix}_{timestamp}.json"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)

    pd.DataFrame(jobs).to_csv(csv_path, index=False)

    print(f"Saved → {csv_path}")
    print(f"Saved → {json_path}")

# ── CLI ──────────────────────────────────────────────────────────────────────

# --- MAIN FIXED ---
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="all")
    parser.add_argument("--country", nargs="+", default=["in"])
    parser.add_argument("--output", default="jobs")
    args = parser.parse_args()

    print("Starting scraper...\n")

    all_jobs = []

    # ALWAYS include all sources
    if args.source in ("adzuna", "all"):
        print("Fetching Adzuna...")
        all_jobs += scrape_adzuna(args.country)

    if args.source in ("indeed", "all"):
        print("Fetching Indeed...")
        all_jobs += scrape_indeed_rss(args.country)

    if args.source in ("linkedin", "all"):
        print("Fetching LinkedIn...")
        all_jobs += scrape_linkedin(args.country)

    print(f"\nTotal raw jobs: {len(all_jobs)}")

    # Deduplicate
    all_jobs = deduplicate(all_jobs)
    print(f"After deduplication: {len(all_jobs)}")

    if not all_jobs:
        print("❌ No jobs found!")
        return

    # Save JSON + CSV
    save(all_jobs, args.output)

    print("\njobs.json now contains data from ALL sources!")


if __name__ == "__main__":
    main()