# import os
# import pandas as pd
# import json
# from langchain_chroma import Chroma
# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_core.documents import Document

# class RAGEngine:
#     def __init__(self, api_key: str = None):
#         db_path = os.path.join(os.path.dirname(__file__), "chroma_db")
        
#         # Use HuggingFace embeddings via LangChain
#         self.embedding_fn = HuggingFaceEmbeddings(
#             model_name="all-MiniLM-L6-v2"
#         )
        
#         # Initialize LangChain Chroma vectorstores
#         self.jobs_vectorstore = Chroma(
#             collection_name="jobs_v2",
#             embedding_function=self.embedding_fn,
#             persist_directory=db_path
#         )
        
#         self.resumes_vectorstore = Chroma(
#             collection_name="resumes_v2",
#             embedding_function=self.embedding_fn,
#             persist_directory=db_path
#         )

#     def _truncate_text(self, text: str, max_length: int = 5000) -> str:
#         return text[:max_length] if text else ""

#     def index_jobs(self, jobs_df: pd.DataFrame):
#         """Index a dataframe of jobs into ChromaDB using LangChain"""
#         if jobs_df.empty:
#             return 0
        
#         docs = []
        
#         for idx, row in jobs_df.iterrows():
#             job_id = f"job_{idx}"
#             title = row.get("title", "Unknown Title")
#             company = row.get("company", "Unknown Company")
#             desc = row.get("description", "")
            
#             # For 4k jobs df, the description might be missing from the provided df we pass
#             # Let's see how it's handled in main app, or we can just embed title + skills
#             # If description is present use it, else use title and skills
#             if not desc:
#                 # Fallback to skills if description not in df
#                 skills = ", ".join(row.get("skills", []))
#                 doc_text = f"Title: {title}\nCompany: {company}\nSkills: {skills}"
#             else:
#                 doc_text = f"Title: {title}\nCompany: {company}\nDescription: {desc}"
                
#             meta = {
#                 "id": job_id,
#                 "title": title,
#                 "company": company,
#                 "type": "job"
#             }
#             docs.append(Document(page_content=self._truncate_text(doc_text), metadata=meta))
            
#         # Add to collection (batching to avoid payload too large issues)
#         batch_size = 100
#         count = 0
#         for i in range(0, len(docs), batch_size):
#             try:
#                 batch = docs[i:i+batch_size]
#                 ids = [doc.metadata["id"] for doc in batch]
#                 self.jobs_vectorstore.add_documents(documents=batch, ids=ids)
#                 count += len(batch)
#             except Exception as e:
#                 print(f"Error adding batch {i}: {e}")
                
#         return count


#     def index_resumes(self, resumes_list: list):
#         """Index a list of resume dictionaries into ChromaDB using LangChain"""
#         if not resumes_list:
#             return 0
            
#         docs = []
        
#         for idx, res in enumerate(resumes_list):
#             res_id = f"resume_{idx}"
#             name = res.get("name", "Unknown")
#             exp = res.get("experience_years", 0)
#             skills = ", ".join(res.get("skills", []))
#             text = res.get("text", "")
            
#             doc_text = f"Name: {name}\nExperience: {exp} years\nSkills: {skills}\nSummary: {text}"
            
#             meta = {
#                 "id": res_id,
#                 "name": name,
#                 "experience": exp,
#                 "type": "resume"
#             }
#             docs.append(Document(page_content=self._truncate_text(doc_text), metadata=meta))
            
#         batch_size = 50
#         count = 0
#         for i in range(0, len(docs), batch_size):
#             try:
#                 batch = docs[i:i+batch_size]
#                 ids = [doc.metadata["id"] for doc in batch]
#                 self.resumes_vectorstore.add_documents(documents=batch, ids=ids)
#                 count += len(batch)
#             except Exception as e:
#                 print(f"Error adding resume batch {i}: {e}")
                
#         return count


#     def query(self, query_text: str, n_results: int = 3, collection: str = "both") -> str:
#         """Query jobs or resumes and return relevant context formatted as string"""
#         context_parts = []
        
#         try:
#             if collection in ["jobs", "both"]:
#                 results = self.jobs_vectorstore.similarity_search(query_text, k=n_results)
#                 if results:
#                     context_parts.append("--- RELEVANT JOB LISTINGS ---")
#                     for doc in results:
#                         meta = doc.metadata
#                         context_parts.append(f"{meta.get('title', 'Job')} at {meta.get('company', 'Company')}:\n{doc.page_content}")
                        
#             if collection in ["resumes", "both"]:
#                 results = self.resumes_vectorstore.similarity_search(query_text, k=n_results)
#                 if results:
#                     context_parts.append("\n--- RELEVANT CANDIDATE RESUMES ---")
#                     for doc in results:
#                         meta = doc.metadata
#                         context_parts.append(f"Candidate {meta.get('name', 'Unknown')}:\n{doc.page_content}")
                        
#         except Exception as e:
#             print(f"Error querying ChromaDB: {e}")
#             return ""
            
#         return "\n\n".join(context_parts)
