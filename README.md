# Jarvis Pro (ML + DL + Neural Networks)

An advanced, professional starter implementation of a Jarvis-style assistant built with:

- Classical ML (`TF-IDF + Logistic Regression`) for robust intent classification
- Deep Learning (`BiLSTM` in PyTorch) for neural text understanding
- Transformer encoder model (`PyTorch TransformerEncoder`) for advanced intent modeling
- Modular command execution and response generation
- Optional speech input/output pipeline
- Conversation memory for context-aware follow-up handling
- FastAPI service mode for backend integration
- Agent runtime with planning + tool execution
- Workspace-safe file and shell operations with permission guardrails
- JWT authentication with RBAC (`viewer`, `operator`, `admin`)
- Async job queue with polling endpoints
- Human approval workflow for sensitive actions
- Persistent vector memory retrieval (TF-IDF similarity)
- Plugin tool loading from `plugins/*.py`
- Web dashboard for jobs/approvals/logs
- WebSocket live event stream for real-time monitoring
- SQLite persistence for users, jobs, approvals, logs, events
- RAG knowledge engine (`rag index`, `rag ask`) for retrieval over your project/docs
- GPU auto-detection and inference device routing
- Local LLM generation integration for RAG (Ollama/LM Studio compatible)

## Features

- Hybrid ensemble inference across ML + BiLSTM + Transformer
- RL-ready policy module scaffold for agent routing optimization
- Intent confidence thresholding for safer responses
- Production-oriented project structure
- Train and run pipeline scripts
- Extensible command router for system actions
- Optional strict wake-word mode (`jarvis`)
- Tool calling for web search, file read/write, directory listing, and shell execution

## Project Structure

`src/jarvis/data/intents.json` - training dataset  
`src/jarvis/ml/train_ml.py` - classical ML trainer  
`src/jarvis/ml/train_dl.py` - deep learning trainer  
`src/jarvis/ml/train_transformer.py` - transformer trainer  
`src/jarvis/rl/train_rl_policy.py` - reinforcement learning policy scaffold  
`src/jarvis/ml/predictor.py` - unified inference layer  
`src/jarvis/core/assistant.py` - orchestration logic  
`src/jarvis/agent/runtime.py` - planner + executor runtime  
`src/jarvis/agent/queue.py` - background job worker  
`src/jarvis/agent/store.py` - persistent jobs/approvals/logs  
`src/jarvis/core/security.py` - user auth + JWT manager  
`src/jarvis/core/accelerator.py` - GPU/accelerator capability detection  
`src/jarvis/core/vector_memory.py` - long-term memory retrieval  
`src/jarvis/rag/engine.py` - retrieval augmented knowledge engine  
`src/jarvis/tools/builtins.py` - real-world tool integrations  
`src/jarvis/main.py` - CLI entrypoint  
`src/jarvis/api/server.py` - REST API server  
`dashboard/` - React + Vite operations dashboard

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Optional advanced retrieval stack:

```bash
pip install -r requirements_optional_ai.txt
```

Detailed deployment instructions:

- See `DEPLOYMENT.md`

## Train Models

```bash
python -m src.jarvis.ml.train_ml
python -m src.jarvis.ml.train_dl
python -m src.jarvis.ml.train_transformer
python -m src.jarvis.rl.train_rl_policy
```

This creates model files in `models/`.

## Run Jarvis

```bash
python -m src.jarvis.main --mode text
```

Use voice mode (requires microphone + audio dependencies):

```bash
python -m src.jarvis.main --mode voice
```

Enable strict wake word:

```bash
python -m src.jarvis.main --mode voice --strict-wake-word
```

## Run As API

```bash
uvicorn src.jarvis.api.server:app --host 0.0.0.0 --port 8000
```

Then call:

- `GET /health`
- `POST /chat` with JSON body: `{"message":"jarvis what time is it"}`
- `POST /jobs` and poll `GET /jobs/{job_id}`
- `POST /approvals/{approval_id}/approve` or `/reject`
- `GET /dashboard`
- `GET /capabilities`
- `POST /rag/index`
- `POST /rag/query`

Use header:

- `Authorization: Bearer <token>`

Get token from:

- `POST /auth/login`

Default users:

- `admin / admin123`
- `operator / operator123`
- `viewer / viewer123`

Create users (admin only):

- `POST /auth/users`

## Real-World Agent Commands (Examples)

- `search latest ai hardware trends`
- `system info`
- `list files .`
- `read file README.md`
- `write file notes/today.txt:::My daily plan`
- `run python --version`
- `rag index .`
- `rag ask where is JWT auth handled`

`POST /chat` now returns `used_tool` so you can observe tool traces.

Sensitive actions (`write_file`, `run_shell`) create pending approvals before execution.

Live events:

- `GET /ws/events?token=<jwt>` (WebSocket)

## Persistence

All state is stored in `data/jarvis.db` (SQLite).

## Frontend Dashboard (React + Vite)

Start backend:

```bash
uvicorn src.jarvis.api.server:app --host 0.0.0.0 --port 8000
```

Start dashboard:

```bash
cd dashboard
npm install
npm run dev
```

Open:

- `http://localhost:5173`

Dashboard supports:

- login + JWT storage
- chat calls
- job submit/poll
- approvals approve/reject
- live WebSocket event stream
- super-intelligence themed animated UI
- system capability panel (GPU/CPU routing view)
- RAG index/query controls

## Boss + Female Voice Persona

- Assistant responses are styled to address you as `Boss`.
- TTS selects a female voice profile when available on your OS voice engine.

## Custom API Integration

Configure your APIs in `data/custom_apis.json`.

Call from chat/jobs:

- `api news latest nvidia launch`

Set secret tokens via environment variables and map with `auth_env` in config.

## Local LLM Integration (for RAG answers)

Configure `data/llm_config.json` and set `"enabled": true`.

Supported providers:

- `ollama` (default)
- `openai_compatible` (LM Studio / vLLM style endpoint)

## One-Click Start (Windows)

From `jarvis_pro/`:

- `run_all.bat`
or
- `powershell -ExecutionPolicy Bypass -File .\run_all.ps1`

This launches backend and dashboard in separate terminals.

## Export Complete Project (Zip)

From `jarvis_pro/`:

- `powershell -ExecutionPolicy Bypass -File .\export_project.ps1`

This creates a full downloadable zip containing everything built so far.

Slim export (excludes heavy/generated folders like `node_modules`, virtual envs, caches, build outputs):

- `powershell -ExecutionPolicy Bypass -File .\export_project_slim.ps1`

## Plugin Tools

Drop plugin files into `plugins/` with:

```python
def register() -> dict:
    return {"tool_name": callable_function}
```

Example included: `plugins/sample_plugin.py`

Invoke plugin tools:

- `plugin echo hello world`

## Notes

- This is an advanced local assistant framework, not a surveillance/backdoor tool.
- Add your own secure integrations (calendar, email, IoT, cloud models) in `core/commands.py`.
- Sub-1-second responses depend on hardware, model size, and local network/API latency.
