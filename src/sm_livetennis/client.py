"""Thin async HTTP client for the Live Tennis API free tier.

Only the free-tier, read-only endpoints are used:

* ``GET /matches?status=live`` — live match state (score, server, break point)
* ``GET /players?search=<name>`` — player lookup (ranking + Elo)
* ``GET /players?ranking=<n>`` — ranked players
* ``GET /fixtures`` — upcoming fixtures

Every response is a JSON object of the shape ``{"data": [...]}``. Authentication
is a single ``X-API-Key`` header. See https://livetennisapi.com for docs and a
free key (no card required).
"""

from __future__ import annotations

from typing import Any

import httpx

DEFAULT_BASE_URL = "https://api.livetennisapi.com/api/public/v1"
DEFAULT_TIMEOUT = 10.0


class LiveTennisError(Exception):
    """Base class for all Live Tennis client errors."""


class AuthError(LiveTennisError):
    """Raised when the API rejects the key (HTTP 401/403)."""


class RateLimitError(LiveTennisError):
    """Raised when the free-tier rate limit is exceeded (HTTP 429)."""


class ApiError(LiveTennisError):
    """Raised for any other non-success response."""


class LiveTennisClient:
    """Small async wrapper around the Live Tennis public API.

    Args:
        api_key: the caller's API key, sent as the ``X-API-Key`` header.
        base_url: override the API base URL (mostly for testing).
        timeout: per-request timeout in seconds.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Perform a GET request and return the ``data`` list from the envelope."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        headers = {"X-API-Key": self.api_key, "Accept": "application/json"}
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.get(url, params=params, headers=headers)
            except httpx.HTTPError as exc:  # network / DNS / timeout
                raise ApiError(f"Could not reach the Live Tennis API: {exc}") from exc

        if resp.status_code in (401, 403):
            raise AuthError("The Live Tennis API rejected the API key (unauthorized).")
        if resp.status_code == 429:
            raise RateLimitError("Live Tennis API rate limit reached. Try again in a moment.")
        if resp.status_code >= 400:
            raise ApiError(f"Live Tennis API returned HTTP {resp.status_code}.")

        try:
            body = resp.json()
        except ValueError as exc:
            raise ApiError("Live Tennis API returned a non-JSON response.") from exc

        data = body.get("data", []) if isinstance(body, dict) else []
        return data if isinstance(data, list) else []

    async def live_matches(self) -> list[dict[str, Any]]:
        """Return the list of currently-live matches."""
        return await self._get("matches", {"status": "live"})

    async def search_players(self, name: str) -> list[dict[str, Any]]:
        """Return players whose name matches ``name``."""
        return await self._get("players", {"search": name})

    async def rankings(self, limit: int = 10) -> list[dict[str, Any]]:
        """Return the top ranked players, sorted by ranking ascending.

        The API is asked for players up to ``limit``; the result is sorted and
        sliced client-side so the output is stable regardless of server order.
        """
        players = await self._get("players", {"ranking": limit})
        ranked = [p for p in players if p.get("ranking") is not None]
        ranked.sort(key=lambda p: p.get("ranking", 10**9))
        return ranked[:limit]

    async def fixtures(self) -> list[dict[str, Any]]:
        """Return upcoming fixtures."""
        return await self._get("fixtures", {"status": "upcoming"})
