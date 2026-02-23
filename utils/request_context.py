from __future__ import annotations

from contextvars import ContextVar

_request_id_var: ContextVar[str] = ContextVar("request_id", default="")

def set_request_id(rid: str) -> None:
    _request_id_var.set(rid or "")

def get_request_id() -> str:
    return _request_id_var.get() or ""

def clear_request_id() -> None:
    _request_id_var.set("")
