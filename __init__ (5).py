from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class ToolCall:
    name: str
    args: Dict[str, str] = field(default_factory=dict)


@dataclass
class AgentResult:
    response: str
    should_exit: bool = False
    used_tool: str | None = None
    requires_approval: bool = False
    approval_id: str | None = None
