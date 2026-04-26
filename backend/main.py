import os
import sys
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# Add the parent directory to the path so we can import rag module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.engine import RAGEngine

app = FastAPI(title="Auto Chaos Engineering Generator using RAG")

# CORS to allow potential frontend later
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = RAGEngine(dataset_path="dataset/incidents.json")

class IncidentRequest(BaseModel):
    issue: str

class IncidentResponse(BaseModel):
    cause: str
    suggested_fix: str
    kubectl_command: str
    chaos_experiment: str

@app.get("/")
def read_root():
    return {"message": "Welcome to Auto Chaos Engineering Generator using RAG!"}

@app.post("/analyze", response_model=IncidentResponse)
def analyze_issue(request: IncidentRequest):
    result = engine.generate(request.issue)
    return IncidentResponse(**result)
