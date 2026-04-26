import json
import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

class RAGEngine:
    def __init__(self, dataset_path="dataset/incidents.json"):
        print("Initializing RAG Engine...")
        self.dataset_path = dataset_path
        self.incidents = []
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = None
        self.load_and_index()
        
    def load_and_index(self):
        if not os.path.exists(self.dataset_path):
            print(f"Dataset not found at {self.dataset_path}")
            return
            
        with open(self.dataset_path, 'r') as f:
            self.incidents = json.load(f)
            
        if not self.incidents:
            return
            
        # Create embeddings for all issue descriptions
        texts = [inc["issue"] + " " + inc["cause"] for inc in self.incidents]
        embeddings = self.model.encode(texts)
        
        # Initialize FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(np.array(embeddings).astype('float32'))
        print(f"Successfully indexed {len(self.incidents)} incidents.")
        
    def retrieve(self, query: str, top_k: int = 1):
        if not self.index:
            return None
            
        query_embedding = self.model.encode([query])
        distances, indices = self.index.search(np.array(query_embedding).astype('float32'), top_k)
        
        best_match_idx = indices[0][0]
        if best_match_idx != -1 and best_match_idx < len(self.incidents):
            return self.incidents[best_match_idx]
        return None

    def generate(self, query: str):
        # 1. Retrieve the most relevant incident from our FAISS vector store
        match = self.retrieve(query)
        
        if not match:
            return {
                "cause": "Unknown issue.",
                "suggested_fix": "Please check general kubernetes logs.",
                "kubectl_command": "kubectl get events",
                "chaos_experiment": "# Not found"
            }
            
        # 2. Check if OpenAI API key is provided
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        
        if openai_api_key:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=openai_api_key)
                
                prompt = f"""
                You are a DevOps assistant. The user reported the following issue: "{query}".
                
                Based on our knowledge base, a similar past incident is:
                Issue: {match['issue']}
                Cause: {match['cause']}
                Fix: {match['suggested_fix']}
                Command: {match['kubectl_command']}
                Chaos YAML:\n{match['chaos_experiment']}
                
                Formulate a helpful, beginner-friendly response providing the cause, suggested fix, kubectl command, and the exact chaos experiment YAML. 
                Output as JSON with keys: cause, suggested_fix, kubectl_command, chaos_experiment.
                """
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={ "type": "json_object" }
                )
                return json.loads(response.choices[0].message.content)
            except Exception as e:
                print(f"OpenAI fallback failed: {e}. Using local rule-based response.")
        
        # 3. Local / Free fallback (Rule-based structured output)
        # We simply format the retrieved data nicely. This ensures the demo always works!
        return {
            "cause": match["cause"],
            "suggested_fix": match["suggested_fix"],
            "kubectl_command": match["kubectl_command"],
            "chaos_experiment": match["chaos_experiment"]
        }
