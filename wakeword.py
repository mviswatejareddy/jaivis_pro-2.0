from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from ..agent.queue import JobQueue
from ..agent.runtime import JarvisAgentRuntime
from ..agent.store import AgentStore
from ..core.assistant import JarvisAssistant
from ..core.security import AuthManager


app = FastAPI(title="Jarvis Pro API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
WORKSPACE = Path(__file__).resolve().parents[3]
DATA_DIR = WORKSPACE / "data"
store = AgentStore(DATA_DIR)
auth = AuthManager(DATA_DIR)
bot = JarvisAssistant()
agent = JarvisAgentRuntime(
    workspace_root=WORKSPACE,
    fallback_assistant=bot,
    store=store,
)
job_queue = JobQueue(workspace_root=WORKSPACE, store=store)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    should_exit: bool
    used_tool: str | None = None
    requires_approval: bool = False
    approval_id: str | None = None


class JobRequest(BaseModel):
    message: str


class ApprovalResponse(BaseModel):
    status: str
    result: str


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str


class RAGIndexRequest(BaseModel):
    path: str = "."
    max_files: int = 200


class RAGQueryRequest(BaseModel):
    question: str
    top_k: int = 3


def get_auth(authorization: str = Header(default="")) -> dict:
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token.")
    token = authorization.split(" ", maxsplit=1)[1]
    payload = auth.verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    return payload


def get_role(payload: dict = Depends(get_auth)) -> str:
    return str(payload.get("role", "viewer"))


@app.post("/auth/login", response_model=LoginResponse)
def login(req: LoginRequest) -> LoginResponse:
    role = auth.authenticate_user(req.username, req.password)
    if not role:
        raise HTTPException(status_code=401, detail="Invalid username/password.")
    token = auth.issue_token(req.username, role)
    return LoginResponse(access_token=token, role=role)


@app.post("/auth/users")
def create_user(req: CreateUserRequest, role: str = Depends(get_role)) -> dict[str, str]:
    if role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can create users.")
    ok = auth.create_user(req.username, req.password, req.role)
    if not ok:
        raise HTTPException(status_code=400, detail="Could not create user.")
    return {"status": "created", "username": req.username, "role": req.role}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "auth": "enabled"}


@app.get("/capabilities")
def capabilities(_: str = Depends(get_role)) -> dict:
    return {"accelerator": agent.accelerator, "llm_enabled": agent.rag.llm.is_enabled()}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, role: str = Depends(get_role)) -> ChatResponse:
    result = agent.handle(req.message, role=role)
    return ChatResponse(
        response=result.response,
        should_exit=result.should_exit,
        used_tool=result.used_tool,
        requires_approval=result.requires_approval,
        approval_id=result.approval_id,
    )


@app.post("/rag/index")
def rag_index(req: RAGIndexRequest, role: str = Depends(get_role)) -> dict:
    if role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can build RAG index.")
    result = agent.rag.index_directory(req.path, max_files=req.max_files)
    store.log("rag_index", {"role": role, "result": result})
    return result


@app.post("/rag/query")
def rag_query(req: RAGQueryRequest, _: str = Depends(get_role)) -> dict:
    result = agent.rag.query(req.question, top_k=req.top_k)
    return result


@app.post("/jobs")
def create_job(req: JobRequest, role: str = Depends(get_role)) -> dict[str, str]:
    job_id = store.create_job(message=req.message, role=role)
    job_queue.submit(job_id=job_id, message=req.message, role=role)
    store.log("job_created", {"job_id": job_id, "role": role})
    return {"job_id": job_id, "status": "queued"}


@app.get("/jobs/{job_id}")
def get_job(job_id: str, _: str = Depends(get_role)) -> dict:
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job


@app.get("/jobs-feed")
def jobs_feed(_: str = Depends(get_role)) -> dict:
    return {"items": store.list_jobs(limit=100)}


@app.post("/approvals/{approval_id}/approve", response_model=ApprovalResponse)
def approve(approval_id: str, role: str = Depends(get_role)) -> ApprovalResponse:
    if role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can approve.")
    approval = store.get_approval(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found.")
    store.set_approval_status(approval_id, "approved")
    result = agent.execute_approved(approval_id=approval_id, role=role)
    return ApprovalResponse(status="approved", result=result.response)


@app.get("/approvals-feed")
def approvals_feed(_: str = Depends(get_role)) -> dict:
    return {"items": store.list_approvals(limit=100)}


@app.post("/approvals/{approval_id}/reject", response_model=ApprovalResponse)
def reject(approval_id: str, role: str = Depends(get_role)) -> ApprovalResponse:
    if role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can reject.")
    approval = store.get_approval(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found.")
    store.set_approval_status(approval_id, "rejected")
    if approval.get("job_id"):
        store.update_job(approval["job_id"], status="failed", result="Approval rejected")
    return ApprovalResponse(status="rejected", result="Approval rejected")


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(_: str = Depends(get_role)) -> str:
    jobs = store.list_jobs(limit=30)
    approvals = store.list_approvals(limit=30)
    logs = store.list_logs(limit=50)
    job_rows = "".join(
        [f"<tr><td>{j['id'][:8]}</td><td>{j['role']}</td><td>{j['status']}</td><td>{(j.get('result') or '')[:60]}</td></tr>" for j in jobs]
    )
    app_rows = "".join(
        [f"<tr><td>{a['id'][:8]}</td><td>{a['action']}</td><td>{a['status']}</td><td>{a.get('job_id')}</td></tr>" for a in approvals]
    )
    log_rows = "".join([f"<li><b>{x['event']}</b> - {str(x['payload'])}</li>" for x in logs[-20:]])
    return f"""
    <html><body style='font-family:Arial;padding:20px'>
    <h2>Jarvis Pro Dashboard</h2>
    <p>Live updates are streamed from <code>/ws/events</code>.</p>
    <h3>Jobs</h3><table border='1' cellpadding='6'><tr><th>ID</th><th>Role</th><th>Status</th><th>Result</th></tr>{job_rows}</table>
    <h3>Approvals</h3><table border='1' cellpadding='6'><tr><th>ID</th><th>Action</th><th>Status</th><th>Job</th></tr>{app_rows}</table>
    <h3>Recent Logs</h3><ul id='logs'>{log_rows}</ul>
    <script>
      const proto = location.protocol === "https:" ? "wss" : "ws";
      const token = localStorage.getItem("jarvis_jwt") || "";
      const ws = new WebSocket(`${{proto}}://${{location.host}}/ws/events?token=${{encodeURIComponent(token)}}`);
      ws.onmessage = (evt) => {{
        try {{
          const data = JSON.parse(evt.data);
          const ul = document.getElementById("logs");
          const li = document.createElement("li");
          li.innerHTML = `<b>${{data.event}}</b> - ${{JSON.stringify(data.payload)}}`;
          ul.prepend(li);
        }} catch (e) {{}}
      }};
    </script>
    </body></html>
    """


@app.websocket("/ws/events")
async def ws_events(websocket: WebSocket, token: str = "") -> None:
    payload = auth.verify_token(token)
    if not payload:
        await websocket.close(code=1008)
        return
    await websocket.accept()
    last_id = 0
    try:
        while True:
            events = store.list_events_after(last_id=last_id, limit=30)
            for ev in events:
                last_id = max(last_id, int(ev["id"]))
                await websocket.send_json(ev)
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        return
