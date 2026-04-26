# Jarvis Pro Deployment Guide (Step-by-Step)

This guide is written for zero-confusion deployment on Windows first, then cloud.

## 1) Local Deployment (Recommended First)

### Prerequisites

- Python 3.10+ installed and available in PATH
- Node.js LTS (includes npm) installed and available in PATH
- Windows PowerShell

Verify:

```powershell
python --version
npm --version
```

### A. Backend setup

```powershell
cd "C:\Users\VISWA\OneDrive\Desktop\VC\jarvis_pro"
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Start backend:

```powershell
python -m uvicorn src.jarvis.api.server:app --host 0.0.0.0 --port 8000
```

Backend should be reachable at:

- <http://localhost:8000/health>
- <http://localhost:8000/docs>

### B. Frontend setup

Open a second terminal:

```powershell
cd "C:\Users\VISWA\OneDrive\Desktop\VC\jarvis_pro\dashboard"
npm install
npm run dev
```

Open:

- <http://localhost:5173>

### C. Login defaults

- `admin / admin123`
- `operator / operator123`
- `viewer / viewer123`

---

## 2) Optional Local LLM (Ollama / LM Studio)

RAG can use local LLM generation if enabled.

### A. Ollama option

1. Install Ollama
2. Pull model:

```powershell
ollama pull llama3.2
```

3. Ensure `data/llm_config.json` has:

```json
{
  "enabled": true,
  "provider": "ollama",
  "base_url": "http://localhost:11434",
  "model": "llama3.2",
  "timeout_sec": 8
}
```

### B. LM Studio / OpenAI-compatible option

Set config:

```json
{
  "enabled": true,
  "provider": "openai_compatible",
  "base_url": "http://localhost:1234/v1",
  "model": "your-local-model-id",
  "api_key": "not-required",
  "timeout_sec": 8
}
```

---

## 3) Production Cloud Deployment (Stable Setup)

Use:

- **Backend**: Render (Web Service)
- **Frontend**: Vercel (Static Site)

### A. Backend on Render

1. Push `jarvis_pro` to GitHub.
2. Create a Render Web Service from repo.
3. Configure:
   - Runtime: Python
   - Build command:
     - `pip install -r requirements.txt`
   - Start command:
     - `python -m uvicorn src.jarvis.api.server:app --host 0.0.0.0 --port $PORT`
4. Add persistent disk (for SQLite/data) if using long-term storage.
5. Update CORS origin in `src/jarvis/api/server.py` to include your Vercel URL.

### B. Frontend on Vercel

1. Import repo in Vercel.
2. Root directory: `dashboard`
3. Build command: `npm run build`
4. Output directory: `dist`
5. In `dashboard/src/App.jsx`, set `API_BASE` to your backend URL before deploy.

---

## 4) Post-Deploy Validation Checklist

- Backend health works
- Login works
- WebSocket stream connects
- Job queue create/poll works
- RAG index + query works
- Approval flow works

---

## 5) Common Error Fixes

- **`npm is not installed`**: install Node.js LTS and restart terminal.
- **`uvicorn not recognized`**: use `python -m uvicorn ...` after venv activation.
- **WebSocket failed**: clear old token and re-login.
- **Login failed**: reset users in SQLite if needed.
