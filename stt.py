from __future__ import annotations

import queue
import threading
from pathlib import Path

from .runtime import JarvisAgentRuntime
from .store import AgentStore
from ..core.assistant import JarvisAssistant


class JobQueue:
    def __init__(self, workspace_root: Path, store: AgentStore) -> None:
        self.store = store
        self.agent = JarvisAgentRuntime(
            workspace_root=workspace_root,
            fallback_assistant=JarvisAssistant(),
            store=store,
        )
        self.q: queue.Queue[tuple[str, str, str]] = queue.Queue()
        self.worker = threading.Thread(target=self._run, daemon=True)
        self.worker.start()

    def submit(self, job_id: str, message: str, role: str) -> None:
        self.q.put((job_id, message, role))

    def _run(self) -> None:
        while True:
            job_id, message, role = self.q.get()
            self.store.update_job(job_id, status="running")
            try:
                self.agent.handle(message, role=role, job_id=job_id)
            except Exception as exc:
                self.store.update_job(job_id, status="failed", result=str(exc))
                self.store.log("job_error", {"job_id": job_id, "error": str(exc)})
            finally:
                self.q.task_done()
