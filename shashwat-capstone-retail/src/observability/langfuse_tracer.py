"""Langfuse tracing wrapper — supports SDK v2 (trace/span) and v3+ (observations)."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Optional
from uuid import uuid4

from src.config import settings


def _hex_trace_id(trace_id: str) -> str:
    cleaned = trace_id.replace("-", "").lower()
    if len(cleaned) == 32:
        return cleaned
    return uuid4().hex


def _parent_span_id() -> str:
    return uuid4().hex[:16]


def _langfuse_disabled() -> bool:
    return os.getenv("LANGFUSE_ENABLED", "false").lower() in ("0", "false", "no")


def _safe_flush(client: Any) -> None:
    try:
        client.flush()
    except Exception:
        pass


class Tracer:
    def __init__(self) -> None:
        self.enabled = False
        self._client = None
        self._api = "none"
        if _langfuse_disabled():
            return
        if not (settings.langfuse_public_key and settings.langfuse_secret_key):
            return
        try:
            from langfuse import Langfuse

            self._client = Langfuse(
                public_key=settings.langfuse_public_key,
                secret_key=settings.langfuse_secret_key,
                host=settings.langfuse_host,
            )
            if hasattr(self._client, "start_as_current_observation"):
                self._api = "v3"
                self.enabled = True
            elif callable(getattr(self._client, "trace", None)):
                self._api = "v2"
                self.enabled = True
        except Exception:
            self.enabled = False
            self._client = None

    def new_trace_id(self) -> str:
        if self._client and hasattr(self._client, "create_trace_id"):
            try:
                return self._client.create_trace_id(seed=str(uuid4()))
            except Exception:
                pass
        return uuid4().hex

    @contextmanager
    def trace(self, name: str, trace_id: Optional[str] = None, metadata: Optional[dict] = None):
        tid = _hex_trace_id(trace_id or self.new_trace_id())
        if not self.enabled or not self._client:
            yield tid
            return

        if self._api == "v3":
            try:
                observation_cm = self._client.start_as_current_observation(
                    as_type="span",
                    name=name,
                    trace_context={"trace_id": tid, "parent_span_id": _parent_span_id()},
                    metadata=metadata or {},
                )
            except Exception:
                yield tid
                return
            try:
                with observation_cm:
                    yield tid
            finally:
                _safe_flush(self._client)
            return

        if self._api == "v2":
            try:
                root = self._client.trace(id=tid, name=name, metadata=metadata or {})
            except Exception:
                yield tid
                return
            try:
                yield tid
            finally:
                try:
                    root.update()
                except Exception:
                    pass
                _safe_flush(self._client)
            return

        yield tid

    def log_span(
        self,
        trace_id: str,
        name: str,
        input_data: Any = None,
        output_data: Any = None,
        metadata: Optional[dict] = None,
    ) -> None:
        if not self.enabled or not self._client:
            return
        tid = _hex_trace_id(trace_id)
        try:
            if self._api == "v3":
                obs = self._client.start_observation(
                    as_type="span",
                    name=name,
                    trace_context={"trace_id": tid, "parent_span_id": _parent_span_id()},
                    input=input_data,
                    metadata=metadata,
                )
                if output_data is not None:
                    obs.update(output=output_data)
                obs.end()
            elif self._api == "v2":
                self._client.span(
                    trace_id=tid,
                    name=name,
                    input=input_data,
                    output=output_data,
                    metadata=metadata,
                )
            _safe_flush(self._client)
        except Exception:
            return


tracer = Tracer()
