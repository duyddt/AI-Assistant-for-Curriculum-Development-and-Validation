"""
base_agent.py — Lop co so cho moi cum SV (Convention 2).

QUAN TRONG: Day la ban trien khai doc lap, viet lai theo mo ta trong
bao_cao_sv7_chi_tiet.md cua Ngoc Thanh. Neu repo goc (apps/ai-services/core)
da co san base_agent.py, HAY DUNG BAN GOC thay vi file nay de dam bao
dong nhat toan he thong — chi dung file nay lam tai lieu tham khao /
placeholder khi test doc lap SV5.

Trach nhiem cua BaseAgent (theo Convention 1, 2, 5, 6):
  1. Nhan request theo dung "envelope" chuan (Convention 1)
  2. Kiem tra cache theo SHA-256 cua payload truoc khi goi execute() (Convention 5)
  3. Goi execute() cua lop con — day la noi chua logic AI thuc su
  4. Bat moi exception, khong de loi "ro ri" ra ngoai dang HTTP 500 tho (Convention 6)
  5. Boc ket qua vao response envelope chuan, kem metadata (Convention 1)
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel, ValidationError

logger = logging.getLogger("tpms_ai.base_agent")


class AgentRequest(BaseModel):
    """Envelope chuan cho request (Convention 1)."""
    run_id: str
    agent_id: str
    program_id: str
    user_id: Optional[str] = None
    payload: dict
    context: dict = {}


class AgentResponse(BaseModel):
    """Envelope chuan cho response (Convention 1)."""
    run_id: str
    agent_id: str
    status: str  # "success" | "partial" | "failed"
    data: Optional[dict] = None
    metadata: dict = {}
    errors: list = []


class SimpleCache:
    """Cache in-memory don gian thay the Redis khi test doc lap.
    Trong production PHAI thay bang RedisCacheManager that (Convention 5)."""

    def __init__(self):
        self._store: dict[str, tuple[float, dict]] = {}

    def get(self, key: str, ttl_seconds: int) -> Optional[dict]:
        item = self._store.get(key)
        if not item:
            return None
        saved_at, value = item
        if time.time() - saved_at > ttl_seconds:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: dict) -> None:
        self._store[key] = (time.time(), value)


_default_cache = SimpleCache()


class BaseAgent(ABC):
    """Moi cum SV ke thua class nay (Convention 2).

    Lop con CHI can override:
      - input_model / output_model (Pydantic schema, Convention 3)
      - cache_ttl_seconds (Convention 5)
      - async def execute(self, payload, context) -> BaseModel
    """

    input_model: type[BaseModel]
    output_model: type[BaseModel]
    cache_ttl_seconds: int = 3600
    agent_name: str = "base"

    def __init__(self):
        self._cache = _default_cache

    # ------------------------------------------------------------------
    # Public entrypoint — day la ham FastAPI router se goi (Convention 8)
    # ------------------------------------------------------------------
    async def run(self, request_data: dict) -> dict:
        started_at = time.perf_counter()

        # 1) Validate envelope
        try:
            request = AgentRequest(**request_data)
        except ValidationError as exc:
            return self._error_envelope(
                run_id=request_data.get("run_id", str(uuid.uuid4())),
                errors=[f"Envelope khong hop le: {exc}"],
            )

        logger.info(
            "agent=%s run_id=%s trace_id=%s BAT DAU",
            self.agent_name, request.run_id, request.context.get("trace_id"),
        )

        # 2) Validate payload theo schema rieng cua SV (Convention 3)
        try:
            payload = self.input_model(**request.payload)
        except ValidationError as exc:
            logger.warning("agent=%s run_id=%s LOI VALIDATION: %s",
                            self.agent_name, request.run_id, exc)
            return self._error_envelope(
                run_id=request.run_id,
                agent_id=request.agent_id,
                errors=[f"Payload khong hop le: {exc}"],
            )

        # 3) Kiem tra cache (Convention 5)
        input_hash = self._hash_payload(request.payload)
        cached = self._cache.get(input_hash, self.cache_ttl_seconds)
        if cached is not None:
            logger.info("agent=%s run_id=%s CACHE HIT", self.agent_name, request.run_id)
            return {
                **cached,
                "run_id": request.run_id,
                "metadata": {**cached.get("metadata", {}), "cached": True},
            }

        # 4) Goi logic AI thuc su — KHONG tu bat exception ben trong execute()
        #    (Convention 6: loi khong phuc hoi phai raise, khong duoc nuot)
        try:
            result: BaseModel = await self.execute(payload, request.context)
        except Exception as exc:  # noqa: BLE001 - day la noi DUY NHAT duoc bat
            logger.error("agent=%s run_id=%s LOI RUNTIME: %s",
                         self.agent_name, request.run_id, exc, exc_info=True)
            return self._error_envelope(
                run_id=request.run_id,
                agent_id=request.agent_id,
                errors=[str(exc)],
            )

        latency_ms = int((time.perf_counter() - started_at) * 1000)
        response = AgentResponse(
            run_id=request.run_id,
            agent_id=request.agent_id,
            status="success",
            data=result.model_dump(),
            metadata={
                "latency_ms": latency_ms,
                "cached": False,
                "input_hash": input_hash,
            },
            errors=[],
        ).model_dump()

        self._cache.set(input_hash, response)
        logger.info("agent=%s run_id=%s HOAN THANH (%dms)",
                    self.agent_name, request.run_id, latency_ms)
        return response

    @abstractmethod
    async def execute(self, payload: BaseModel, context: dict) -> BaseModel:
        """Logic AI thuc su. Lop con PHAI override ham nay."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _hash_payload(payload: dict) -> str:
        canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def _error_envelope(run_id: str, errors: list[str], agent_id: str = "unknown") -> dict:
        return AgentResponse(
            run_id=run_id,
            agent_id=agent_id,
            status="failed",
            data=None,
            metadata={},
            errors=errors,
        ).model_dump()
