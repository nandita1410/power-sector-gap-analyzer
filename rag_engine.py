import os
import chromadb
from chromadb.utils import embedding_functions
import pandas as pd
import json

class RAGEngine:
    def __init__(self, api_key: str = None):
        # Create persistent ChromaDB client
        db_path = os.path.join(os.path.dirname(__file__), "chroma_db")
        self.client = chromadb.PersistentClient(path=db_path)
        
        # Use completely free local embeddings via sentence-transformers
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        
        # Get or create collections
        self.jobs_collection = self.client.get_or_create_collection(
            name="jobs_v2",
            embedding_function=self.embedding_fn
        )
        
        self.resumes_collection = self.client.get_or_create_collection(
            name="resumes_v2",
            embedding_function=self.embedding_fn
        )

    def _truncate_text(self, text: str, max_length: int = 5000) -> str:
        return text[:max_length] if text else ""

    def index_jobs(self, jobs_df: pd.DataFrame):
        """Index a dataframe of jobs into ChromaDB"""
        if jobs_df.empty:
            return 0
        
        ids = []
        documents = []
        metadatas = []
        
        for idx, row in jobs_df.iterrows():
            job_id = f"job_{idx}"
            title = row.get("title", "Unknown Title")
            company = row.get("company", "Unknown Company")
            desc = row.get("description", "")
            
            # For 4k jobs df, the description might be missing from the provided df we pass
            # Let's see how it's handled in main app, or we can just embed title + skills
            # If description is present use it, else use title and skills
            if not desc:
                # Fallback to skills if description not in df
                skills = ", ".join(row.get("skills", []))
                doc_text = f"Title: {title}\nCompany: {company}\nSkills: {skills}"
            else:
                doc_text = f"Title: {title}\nCompany: {company}\nDescription: {desc}"
                
            ids.append(job_id)
            documents.append(self._truncate_text(doc_text))
            
            # Store metadata
            meta = {
                "title": title,
                "company": company,
                "type": "job"
            }
            metadatas.append(meta)
            
        # Add to collection (batching to avoid payload too large issues)
        batch_size = 100
        count = 0
        for i in range(0, len(ids), batch_size):
            try:
                self.jobs_collection.upsert(
                    ids=ids[i:i+batch_size],
                    documents=documents[i:i+batch_size],
                    metadatas=metadatas[i:i+batch_size]
                )
                count += len(ids[i:i+batch_size])
            except Exception as e:
                print(f"Error adding batch {i}: {e}")
                
        return count


    def index_resumes(self, resumes_list: list):
        """Index a list of resume dictionaries into ChromaDB"""
        if not resumes_list:
            return 0
            
        ids = []
        documents = []
        metadatas = []
        
        for idx, res in enumerate(resumes_list):
            res_id = f"resume_{idx}"
            name = res.get("name", "Unknown")
            exp = res.get("experience_years", 0)
            skills = ", ".join(res.get("skills", []))
            text = res.get("text", "")
            
            doc_text = f"Name: {name}\nExperience: {exp} years\nSkills: {skills}\nSummary: {text}"
            
            ids.append(res_id)
            documents.append(self._truncate_text(doc_text))
            
            meta = {
                "name": name,
                "experience": exp,
                "type": "resume"
            }
            metadatas.append(meta)
            
        batch_size = 50
        count = 0
        for i in range(0, len(ids), batch_size):
            try:
                self.resumes_collection.upsert(
                    ids=ids[i:i+batch_size],
                    documents=documents[i:i+batch_size],
                    metadatas=metadatas[i:i+batch_size]
                )
                count += len(ids[i:i+batch_size])
            except Exception as e:
                print(f"Error adding resume batch {i}: {e}")
                
        return count


    def query(self, query_text: str, n_results: int = 3, collection: str = "both") -> str:
        """Query jobs or resumes and return relevant context formatted as string"""
        context_parts = []
        
        try:
            if collection in ["jobs", "both"]:
                results = self.jobs_collection.query(
                    query_texts=[query_text],
                    n_results=n_results
                )
                if results and results['documents'] and results['documents'][0]:
                    context_parts.append("--- RELEVANT JOB LISTINGS ---")
                    for doc, meta in zip(results['documents'][0], results['metadatas'][0] or []):
                        context_parts.append(f"{meta.get('title', 'Job')} at {meta.get('company', 'Company')}:\n{doc}")
                        
            if collection in ["resumes", "both"]:
                results = self.resumes_collection.query(
                    query_texts=[query_text],
                    n_results=n_results
                )
                if results and results['documents'] and results['documents'][0]:
                    context_parts.append("\n--- RELEVANT CANDIDATE RESUMES ---")
                    for doc, meta in zip(results['documents'][0], results['metadatas'][0] or []):
                        context_parts.append(f"Candidate {meta.get('name', 'Unknown')}:\n{doc}")
                        
        except Exception as e:
            print(f"Error querying ChromaDB: {e}")
            return ""
            
        return "\n\n".join(context_parts)
