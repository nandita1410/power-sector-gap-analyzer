#  InsAnalytics: Power Sector Skill Gap Analyzer

## Executive Summary
The **Power Sector Skill Gap Analyzer** is a comprehensive, AI-driven intelligence platform designed to benchmark India's power and energy sector workforce against global standards (US, UK, Australia, EU). 

By ingesting live job market data and processing candidate resumes, the tool identifies critical skill deficits, tracks emerging technology trends, and provides actionable business recommendations. It empowers stakeholders to make data-backed decisions on upskilling, curriculum reform, and strategic hiring.

---

##  Key Features & Capabilities

### 1. Global Market Benchmarking
*   **Cross-Country Comparison:** Compares skill demand in India against first-world markets to highlight the relative "Skill Deficit" or "Surplus".
*   **Offshore Detection Logic:** Smartly identifies and isolates offshore/remote roles (e.g., jobs posted in India but serving US/UK time zones) to ensure domestic statistics are not artificially inflated.
*   **Gap Scoring:** Generates a dynamic 0-100 index representing the divergence between local supply and global demand.

### 2. Generative AI & Retrieval-Augmented Generation (RAG)
*   **⚡ PowerBot:** An embedded, context-aware AI analyst powered by the **Groq API (Llama 3)**.
*   **RAG Engine:** Indexes thousands of jobs and resumes locally, allowing users to query the dashboard via natural language (e.g., *"What is the demand for BESS globally?"*).
*   **LLM Resume Parsing:** Utilizes LLMs to extract deeply technical, nuanced skillsets from raw resume text, outperforming traditional keyword matching.

### 3. Automated Data Ingestion
*   **Multi-Source Scraper:** Automatically fetches job listings from the Adzuna API, Indeed RSS feeds, and LinkedIn public searches.
*   **Deduplication & Cleansing:** Ensures high-fidelity data by automatically dropping duplicate postings across platforms.

### 4. Advanced Taxonomy Engine
*   Categorizes hundreds of technical skills into 6 primary domains:
    *   *Traditional Power Engineering*
    *   *Renewables & Energy Transition*
    *   *Digital & Analytics*
    *   *Grid Modernization*
    *   *Project & Commercial*
    *   *Sustainability & Policy*

---

## Dashboard Modules

The user interface is built with **Streamlit** and features interactive **Plotly** visualizations, divided into several analytical modules:

1.  **🏆 Market Demand:** Heatmaps and bar charts detailing the most requested skills by employers.
2.  **🌍 Cross-Country:** Head-to-head comparison of skill demand between India, US, UK, and Australia.
3.  **📊 Demand vs Supply:** Visual mapping of employer requirements vs. actual talent pool capabilities.
4.  **🔍 India Gap:** Deep-dive into the specific skills where India lags behind global benchmarks (e.g., Digital Twin, OT Cybersecurity).
5.  **⚡ Emerging Tech:** Tracks the adoption rate of next-gen technologies (BESS, Green Hydrogen, Smart Meters) across different geographies.
6.  **💡 Recommendations:** Algorithmic business recommendations categorizing interventions into Immediate, Short-term, and Long-term strategies.
7.  **📋 Raw Data:** Transparent view into the underlying job listings and parsed resumes.

---

##  Technical Architecture

*   **Frontend / UI:** Streamlit, CSS (Glassmorphism, Dark-mode aesthetics)
*   **Visualizations:** Plotly Express & Plotly Graph Objects
*   **LLM Provider:** Groq Cloud (Llama 3 models)
*   **Embeddings & Vector Store:** LangChain, HuggingFace Embeddings, FAISS/ChromaDB
*   **Data Processing:** Pandas, Regex, BeautifulSoup4

---

## Setup & Installation

### Prerequisites
*   Python 3.10+
*   A valid **Groq API Key** (for the AI Chatbot and Resume LLM Parsing)
*   *Optional:* Adzuna API App ID and Key (for the scraper)

### Installation Steps

1. **Clone the repository and navigate to the directory:**
   ```bash
   git clone <repository_url>
   cd power-sector-gap-analyzer
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *Note: If you plan to parse PDF resumes, ensure `pdfplumber` is installed: `pip install pdfplumber`*

3. **Run the Data Scraper (Optional):**
   To fetch fresh job data across multiple countries:
   ```bash
   python scraper.py --country in us gb au de ca
   ```
   This will output a timestamped `jobs_YYYYMMDD_HHMMSS.json` file.

4. **Launch the Dashboard:**
   ```bash
   python -m streamlit run power_sector_dashboard.py
   ```

5. **API Key Configuration:**
   Once the dashboard loads in your browser, enter your **Groq API Key** in the sidebar to enable the PowerBot chatbot and advanced resume processing.

---

##  Project Structure

*   **`power_sector_dashboard.py`**: The main Streamlit application and UI logic.
*   **`scraper.py`**: Multi-source data extraction pipeline.
*   **`constants.py`**: Stores the skill taxonomy, geographic mapping, offshore phrases, and fallback demo data.
*   **`rag_engine.py`**: Handles document chunking, embeddings, and vector store operations for the chatbot.
*   **`style.css`**: Custom CSS for premium, dark-mode dashboard aesthetics.
*   **`jobs_*.json / csv`**: Output datasets generated by the scraper.