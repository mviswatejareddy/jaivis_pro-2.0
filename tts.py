from __future__ import annotations

from pathlib import Path

from .plugins import load_plugins
from .planner import plan_tool
from .schemas import AgentResult
from .store import AgentStore
from ..core.accelerator import get_accelerator_info
from ..core.assistant import JarvisAssistant
from ..core.vector_memory import VectorMemory
from ..rag.engine import RAGEngine
from ..tools.builtins import BuiltinTools


class JarvisAgentRuntime:
    def __init__(
        self,
        workspace_root: Path,
        fallback_assistant: JarvisAssistant | None = None,
        store: AgentStore | None = None,
    ) -> None:
        self.tools = BuiltinTools(workspace_root=workspace_root)
        self.fallback = fallback_assistant or JarvisAssistant()
        self.store = store or AgentStore(workspace_root / "data")
        self.vmem = VectorMemory(workspace_root / "data")
        self.plugins = load_plugins(workspace_root / "plugins")
        self.rag = RAGEngine(workspace_root=workspace_root)
        self.accelerator = get_accelerator_info()

    @staticmethod
    def _as_boss(text: str) -> str:
        if not text:
            return text
        return text if "boss" in text.lower() else f"{text} Boss."

    def _allowed(self, role: str, tool_name: str) -> bool:
        rules = {
            "viewer": {"now", "system_info", "web_search", "read_file", "list_dir", "api_call", "rag_query"},
            "operator": {"now", "system_info", "web_search", "read_file", "list_dir", "write_file", "api_call", "rag_query"},
            "admin": {"now", "system_info", "web_search", "read_file", "list_dir", "write_file", "run_shell", "api_call", "rag_query", "rag_index"},
        }
        return tool_name in rules.get(role, set()) or tool_name in self.plugins

    def _needs_approval(self, tool_name: str) -> bool:
        return tool_name in {"run_shell", "write_file"}

    def handle(self, user_text: str, role: str = "admin", job_id: str | None = None) -> AgentResult:
        self.vmem.add(user_text, {"type": "user"})
        plan = plan_tool(user_text)
        if not plan:
            hints = self.vmem.query(user_text, top_k=2)
            augmented = user_text if not hints else f"{user_text}\nContext hints: {' | '.join(hints)}"
            response, should_exit = self.fallback.handle(augmented)
            self.vmem.add(response, {"type": "assistant"})
            self.store.log("chat_fallback", {"role": role, "message": user_text})
            if job_id:
                self.store.update_job(job_id, status="done", result=response)
            return AgentResult(response=response, should_exit=should_exit, used_tool=None)

        if plan.name == "exit":
            self.store.log("exit", {"role": role})
            if job_id:
                self.store.update_job(job_id, status="done", result="Shutting down agent runtime.")
            return AgentResult(response="Shutting down agent runtime.", should_exit=True, used_tool="exit")

        if not self._allowed(role, plan.name):
            msg = f"Role '{role}' is not allowed to use tool '{plan.name}'."
            self.store.log("rbac_block", {"role": role, "tool": plan.name})
            if job_id:
                self.store.update_job(job_id, status="failed", result=msg)
            return AgentResult(response=msg, should_exit=False, used_tool=plan.name)

        if self._needs_approval(plan.name):
            aid = self.store.create_approval(job_id=job_id or "adhoc", action=plan.name, payload=plan.args)
            msg = f"Action '{plan.name}' pending approval: {aid}"
            self.store.log("approval_required", {"approval_id": aid, "tool": plan.name, "args": plan.args})
            if job_id:
                self.store.update_job(job_id, status="awaiting_approval", result=msg)
            return AgentResult(
                response=msg,
                used_tool=plan.name,
                requires_approval=True,
                approval_id=aid,
            )

        if plan.name in self.plugins:
            out = self.plugins[plan.name](plan.args.get("query", "") or user_text)
            self.store.log("plugin_tool", {"tool": plan.name, "role": role})
            if job_id:
                self.store.update_job(job_id, status="done", result=out)
            return AgentResult(response=out, used_tool=plan.name)

        if plan.name == "now":
            out = self.tools.now()
            self.store.log("tool_call", {"tool": plan.name, "role": role})
            if job_id:
                self.store.update_job(job_id, status="done", result=out)
            return AgentResult(response=self._as_boss(out), used_tool=plan.name)
        if plan.name == "system_info":
            out = f"{self.tools.system_info()} | accelerator={self.accelerator}"
            self.store.log("tool_call", {"tool": plan.name, "role": role})
            if job_id:
                self.store.update_job(job_id, status="done", result=out)
            return AgentResult(response=self._as_boss(out), used_tool=plan.name)
        if plan.name == "web_search":
            out = self.tools.web_search(plan.args.get("query", ""))
            self.store.log("tool_call", {"tool": plan.name, "role": role})
            if job_id:
                self.store.update_job(job_id, status="done", result=out)
            return AgentResult(response=self._as_boss(out), used_tool=plan.name)
        if plan.name == "read_file":
            out = self.tools.read_file(plan.args.get("path", ""))
            self.store.log("tool_call", {"tool": plan.name, "role": role})
            if job_id:
                self.store.update_job(job_id, status="done", result=out)
            return AgentResult(response=self._as_boss(out), used_tool=plan.name)
        if plan.name == "list_dir":
            out = self.tools.list_dir(plan.args.get("path", "."))
            self.store.log("tool_call", {"tool": plan.name, "role": role})
            if job_id:
                self.store.update_job(job_id, status="done", result=out)
            return AgentResult(response=self._as_boss(out), used_tool=plan.name)
        if plan.name == "write_file":
            out = self.tools.write_file(plan.args.get("payload", ""))
            self.store.log("tool_call", {"tool": plan.name, "role": role})
            if job_id:
                self.store.update_job(job_id, status="done", result=out)
            return AgentResult(response=self._as_boss(out), used_tool=plan.name)
        if plan.name == "run_shell":
            out = self.tools.run_shell(plan.args.get("command", ""))
            self.store.log("tool_call", {"tool": plan.name, "role": role})
            if job_id:
                self.store.update_job(job_id, status="done", result=out)
            return AgentResult(response=self._as_boss(out), used_tool=plan.name)
        if plan.name == "api_call":
            out = self.tools.call_external_api(plan.args.get("payload", ""))
            self.store.log("tool_call", {"tool": plan.name, "role": role})
            if job_id:
                self.store.update_job(job_id, status="done", result=out)
            return AgentResult(response=self._as_boss(out), used_tool=plan.name)
        if plan.name == "rag_index":
            out_obj = self.rag.index_directory(plan.args.get("path", "."))
            out = f"RAG index complete: {out_obj}"
            self.store.log("tool_call", {"tool": plan.name, "role": role, "result": out_obj})
            if job_id:
                self.store.update_job(job_id, status="done", result=out)
            return AgentResult(response=self._as_boss(out), used_tool=plan.name)
        if plan.name == "rag_query":
            out_obj = self.rag.query(plan.args.get("query", ""), top_k=3)
            out = out_obj.get("answer", "")
            self.store.log("tool_call", {"tool": plan.name, "role": role, "sources": out_obj.get("sources", [])})
            if job_id:
                self.store.update_job(job_id, status="done", result=out)
            return AgentResult(response=self._as_boss(out), used_tool=plan.name)

        response, should_exit = self.fallback.handle(user_text)
        self.vmem.add(response, {"type": "assistant"})
        self.store.log("chat_fallback", {"role": role, "message": user_text})
        if job_id:
            self.store.update_job(job_id, status="done", result=response)
        return AgentResult(response=response, should_exit=should_exit, used_tool=None)

    def execute_approved(self, approval_id: str, role: str = "admin") -> AgentResult:
        approval = self.store.get_approval(approval_id)
        if not approval:
            return AgentResult(response="Approval id not found.")
        if approval.get("status") != "approved":
            return AgentResult(response="Approval is not approved yet.")
        action = approval.get("action")
        args = approval.get("payload", {})
        job_id = approval.get("job_id")
        if action == "run_shell":
            out = self.tools.run_shell(args.get("command", ""))
        elif action == "write_file":
            out = self.tools.write_file(args.get("payload", ""))
        else:
            out = "Unsupported approval action."
        self.store.log("approved_execution", {"approval_id": approval_id, "action": action, "role": role})
        if job_id:
            self.store.update_job(job_id, status="done", result=out)
        return AgentResult(response=out, used_tool=action)
