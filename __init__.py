from __future__ import annotations


def echo_tool(query: str) -> str:
    return f"[sample_plugin.echo] {query or 'no input provided'}"


def register() -> dict:
    return {"echo": echo_tool}
