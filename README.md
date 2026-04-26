# Auto Chaos Engineering Generator using RAG

This project is an AI-powered DevOps system that combines Retrieval-Augmented Generation (RAG) with Chaos Engineering to test and improve system resilience.

## Architecture

1. **Backend**: FastAPI
2. **RAG Engine**: FAISS for vector storage, `sentence-transformers` for local embeddings.
3. **LLM**: Rule-based fallback or OpenAI integration (if API key provided).
4. **Kubernetes**: Minikube or k3d.
5. **Chaos Tool**: Chaos Mesh for running chaos experiments locally.

## Setup Instructions

### 1. Prerequisites

- Docker Desktop / Rancher Desktop (for running Minikube/k3d)
- Minikube or k3d installed
- `kubectl` installed
- Python 3.9+
- Helm (for Chaos Mesh)

### 2. Install Dependencies

```bash
python -m venv venv
# On Windows: venv\Scripts\activate
# On Mac/Linux: source venv/bin/activate

pip install -r requirements.txt
```

### 3. Setup Kubernetes & Demo App

```bash
# Start Minikube
minikube start

# Deploy Sample App
kubectl apply -f k8s/demo-app.yaml

# Check pods
kubectl get pods
```

### 4. Install Chaos Mesh (for running experiments)

```bash
helm repo add chaos-mesh https://charts.chaos-mesh.org
helm repo update
helm install chaos-mesh chaos-mesh/chaos-mesh -n=chaos-mesh --create-namespace --set dashboard.securityMode=false
```
*Wait for chaos-mesh pods to be running:*
```bash
kubectl get pods -n chaos-mesh
```

### 5. Start Backend API

```bash
# Run from the project root
uvicorn backend.main:app --reload
```
The API will be available at `http://127.0.0.1:8000`.

### 6. Test the RAG API

```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d "{\"issue\": \"CrashLoopBackOff\"}"
```

**Expected Output:**
```json
{
  "cause": "The application inside the pod is crashing immediately after startup. This is often due to misconfiguration, missing dependencies, or lack of resources.",
  "suggested_fix": "Check the pod logs to identify the exact error. Increase resource limits if it is an OOM issue.",
  "kubectl_command": "kubectl logs <pod-name> --previous",
  "chaos_experiment": "..."
}
```

### 7. Run a Chaos Experiment Locally

You can test the generated YAML or use one of the pre-built examples:

```bash
# Apply pod deletion chaos
kubectl apply -f chaos/pod-delete.yaml

# Observe the pod restarting
kubectl get pods -w
```

## Demo Steps (Interview Presentation)

1. **Explain Project**: "This system uses RAG to analyze DevOps issues and generate chaos experiments to test resilience."
2. **Show Running App**: `kubectl get pods`
3. **Run RAG**: Send input to the API: `curl -X POST http://127.0.0.1:8000/analyze -d '{"issue": "CrashLoopBackOff"}' -H "Content-Type: application/json"`
4. **Show Output**: Explain the returned cause, fix, and chaos YAML.
5. **Show Chaos Test**: `kubectl apply -f chaos/pod-delete.yaml`
6. **Conclusion**: "This proves the system can detect issues, suggest fixes, and validate resilience."
"# CEG" 
