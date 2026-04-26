from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests


class LocalLLMClient:
    """
    Config-driven local LLM client.
    Supports:
      - Ollama (/api/generate)
      - OpenAI-compatible local servers (LM Studio / vLLM / etc)
    """

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root
        self.cfg_path = workspace_root / "data" / "llm_config.json"
        self.cfg = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        if not self.cfg_path.exists():
            return {
                "enabled": False,
                "provider": "ollama",
                "base_url": "http://localhost:11434",
                "model": "llama3.2",
                "timeout_sec": 8,
            }
        try:
            return json.loads(self.cfg_path.read_text(encoding="utf-8"))
        except Exception:
            return {"enabled": False}

    def is_enabled(self) -> bool:
        return bool(self.cfg.get("enabled", False))

    def generate(self, prompt: str) -> str:
        provider = str(self.cfg.get("provider", "ollama")).lower().strip()
        if provider == "openai_compatible":
            return self._generate_openai_compatible(prompt)
        return self._generate_ollama(prompt)

    def _generate_ollama(self, prompt: str) -> str:
        base = str(self.cfg.get("base_url", "http://localhost:11434")).rstrip("/")
        model = str(self.cfg.get("model", "llama3.2"))
        timeout_sec = int(self.cfg.get("timeout_sec", 8))
        r = requests.post(
            f"{base}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=timeout_sec,
        )
        r.raise_for_status()
        data = r.json()
        return str(data.get("response", "")).strip()

    def _generate_openai_compatible(self, prompt: str) -> str:
        base = str(self.cfg.get("base_url", "http://localhost:1234/v1")).rstrip("/")
        model = str(self.cfg.get("model", "local-model"))
        timeout_sec = int(self.cfg.get("timeout_sec", 8))
        api_key = str(self.cfg.get("api_key", "not-required"))
        r = requests.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are JARVIS. Address user as Boss briefly."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
            },
            timeout=timeout_sec,
        )
        r.raise_for_status()
        data = r.json()
        return str(data["choices"][0]["message"]["content"]).strip()
