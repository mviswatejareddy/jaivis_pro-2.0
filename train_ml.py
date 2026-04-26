from __future__ import annotations

import ast
import datetime as dt
from typing import Callable, Dict


def _safe_eval(expr: str) -> float:
    allowed_nodes = (
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Num,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Pow,
        ast.Mod,
        ast.USub,
        ast.UAdd,
        ast.Constant,
    )
    tree = ast.parse(expr, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, allowed_nodes):
            raise ValueError("Unsupported operation in expression.")
    return float(eval(compile(tree, "<expr>", "eval"), {"__builtins__": {}}, {}))


def get_time(_: str) -> str:
    return dt.datetime.now().strftime("Current time: %H:%M:%S")


def get_date(_: str) -> str:
    return dt.datetime.now().strftime("Today's date: %A, %d %B %Y")


def system_status(_: str) -> str:
    return "System status is healthy. Models and runtime are active."


def calculate(user_text: str) -> str:
    cleaned = (
        user_text.lower()
        .replace("calculate", "")
        .replace("evaluate", "")
        .replace("solve", "")
        .replace("compute", "")
        .replace("plus", "+")
        .replace("minus", "-")
        .replace("x", "*")
        .replace("times", "*")
        .replace("divided by", "/")
        .replace("power", "**")
        .strip()
    )
    try:
        result = _safe_eval(cleaned)
        return f"Result: {result:g}"
    except Exception:
        return "I could not parse that expression safely. Try a simpler math expression."


COMMANDS: Dict[str, Callable[[str], str]] = {
    "time_query": get_time,
    "date_query": get_date,
    "system_status": system_status,
    "math_eval": calculate,
}
