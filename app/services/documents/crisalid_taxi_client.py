"""
HTTP client for the Crisalid-taxi semantic classification service.
"""
import asyncio
import time
from dataclasses import dataclass, field
from typing import ClassVar

import aiohttp
from loguru import logger

from app.config import get_app_settings


@dataclass
class TaxiMatch:
    """One concept match returned by Crisalid-taxi."""

    concept_uid: str
    rel_type: str
    value: float


@dataclass
class TaxiMatchResponse:
    """Parsed response of ``POST /api/v1/match/``, matches keyed by input id."""

    model: str
    results: dict[str, list[TaxiMatch]] = field(default_factory=dict)


class CrisalidTaxiClient:
    """
    Client for ``POST /api/v1/match/`` with a dedicated timeout and a process-wide
    circuit breaker: after ``taxi_max_consecutive_failures`` consecutive failures,
    calls are suspended for ``taxi_circuit_open_seconds``.

    ``match()`` never raises: every failure is logged and reported as ``None``.
    """

    MATCH_PATH: ClassVar[str] = "/api/v1/match/"

    _consecutive_failures: ClassVar[int] = 0
    _open_until: ClassVar[float | None] = None

    def __init__(self):
        self.settings = get_app_settings()
        if not self.settings.taxi_api_url:
            raise ValueError("TAXI_API_URL must be set when TAXI_ENABLED is true")
        self._url = self.settings.taxi_api_url.rstrip("/") + self.MATCH_PATH
        self._timeout = aiohttp.ClientTimeout(total=self.settings.taxi_timeout_seconds)

    @classmethod
    def is_open(cls) -> bool:
        """
        :return: True while the circuit breaker suspends calls
        """
        return cls._open_until is not None and time.monotonic() < cls._open_until

    @classmethod
    def reset(cls) -> None:
        """Close the circuit breaker and forget past failures."""
        cls._consecutive_failures = 0
        cls._open_until = None

    async def match(self, inputs: list[dict]) -> TaxiMatchResponse | None:
        """
        Classify a list of ``{"id": ..., "text": ...}`` inputs.

        :param inputs: list of inputs with a caller-chosen id
        :return: the parsed response, or None on any failure or while the circuit is open
        """
        if self.is_open():
            logger.debug("Crisalid-taxi circuit open, skipping call for {} inputs", len(inputs))
            return None
        payload = {
            "inputs": inputs,
            "similarity_threshold": self.settings.taxi_similarity_threshold,
        }
        try:
            data = await self._post(payload)
            response = self._parse(data)
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError, TypeError, KeyError) as e:
            self._record_failure(
                f"{type(e).__name__}: {e}",
                max_failures=self.settings.taxi_max_consecutive_failures,
                open_seconds=self.settings.taxi_circuit_open_seconds,
            )
            return None
        self.reset()
        return response

    async def _post(self, payload: dict) -> dict:
        if self.settings.app_env == "TEST" and not hasattr(aiohttp.ClientSession, "mock_calls"):
            raise RuntimeError("In TEST environment, aiohttp.ClientSession must be mocked")
        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            async with session.post(self._url, json=payload) as response:
                if response.status != 200:
                    detail = await response.text()
                    raise ValueError(f"HTTP {response.status} from Crisalid-taxi: {detail[:500]}")
                return await response.json()

    @staticmethod
    def _parse(data: dict) -> TaxiMatchResponse:
        model = data["model"]
        results: dict[str, list[TaxiMatch]] = {}
        for result in data["results"]:
            results[result["id"]] = [
                TaxiMatch(
                    concept_uid=match["concept_uid"],
                    rel_type=match["rel_type"],
                    value=float(match["value"]),
                )
                for match in result.get("matches", [])
            ]
        return TaxiMatchResponse(model=model, results=results)

    @classmethod
    def _record_failure(cls, reason: str, max_failures: int, open_seconds: int) -> None:
        cls._consecutive_failures += 1
        logger.error("Crisalid-taxi call failed ({} consecutive): {}",
                     cls._consecutive_failures, reason)
        if cls._consecutive_failures >= max_failures:
            cls._open_until = time.monotonic() + open_seconds
            logger.warning(
                "Crisalid-taxi circuit opened after {} consecutive failures; "
                "calls suspended for {} s",
                cls._consecutive_failures, open_seconds,
            )
