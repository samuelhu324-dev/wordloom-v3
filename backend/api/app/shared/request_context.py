from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class RequestContext:
    """Request-scoped context for observability.

    Keep this in `api.app.shared` so routers/use-cases/adapters can share it,
    while domain remains infrastructure-agnostic.
    """

    correlation_id: str
    actor_id: Optional[UUID] = None
    workspace_id: Optional[UUID] = None
    route: Optional[str] = None
    method: Optional[str] = None


_request_context_var: ContextVar[Optional[RequestContext]] = ContextVar(
    "wordloom_request_context",
    default=None,
)


def set_request_context(ctx: RequestContext) -> Token[Optional[RequestContext]]:
    return _request_context_var.set(ctx)


def get_request_context() -> Optional[RequestContext]:
    return _request_context_var.get()


def reset_request_context(token: Token[Optional[RequestContext]]) -> None:
    _request_context_var.reset(token)


def with_actor_id(actor_id: Optional[UUID]) -> None:
    """Attach actor_id to current request context (best-effort).

    Safe to call even when no request context exists.
    """

    ctx = get_request_context()
    if not ctx:
        return
    if ctx.actor_id == actor_id:
        return
    set_request_context(
        RequestContext(
            correlation_id=ctx.correlation_id,
            actor_id=actor_id,
            workspace_id=ctx.workspace_id,
            route=ctx.route,
            method=ctx.method,
        )
    )
