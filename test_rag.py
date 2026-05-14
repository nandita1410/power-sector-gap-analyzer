import pandas as pd
from rag_engine import RAGEngine
import os

api_key = "AIzaSyBWKV0tJU89iMcRq3ak9-ssNYRAiRnlj2s"
# Use a fake api key or existing
engine = RAGEngine(api_key=api_key)

dummy_jobs = pd.DataFrame([{"title": "Test Engineer", "company": "Test Co", "description": "Testing"}])
print("Indexing job...")
c = engine.index_jobs(dummy_jobs)
print(f"Result jobs: {c}")

dummy_resumes = [{"name": "Test User", "experience_years": 5, "skills": ["Python"], "text": "Testing"}]
print("Indexing resume...")
r = engine.index_resumes(dummy_resumes)
print(f"Result resumes: {r}")
