# Power Sector Skill Gap Analyzer

## Overview
This project collects job data from:
- Adzuna API
- Indeed RSS
- LinkedIn

Scrape job listings from online platforms across first-world countries (US, UK, Australia, EU) as well as India, targeting power sector roles. The goal is to compare what advanced nations are demanding from their workforce against what the Indian market is asking for — and surface the skill gap.

## Features
- Multi-source job scraping
- Skill extraction
- Country-wise analysis

## How to Run
```bash
pip install wordcloud
pip install -r requirements.txt
python scraper.py --country in us gb au
python -m streamlit run app.py