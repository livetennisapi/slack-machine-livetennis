import httpx
import pytest
import respx

from sm_livetennis.client import (
    ApiError,
    AuthError,
    LiveTennisClient,
    RateLimitError,
)

BASE = "https://api.livetennisapi.com/api/public/v1"


def make_client():
    return LiveTennisClient("test-key", base_url=BASE)


@respx.mock
async def test_live_matches_sends_key_and_returns_data():
    route = respx.get(f"{BASE}/matches").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "m1"}]})
    )
    client = make_client()
    data = await client.live_matches()
    assert data == [{"id": "m1"}]
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == "test-key"
    assert request.url.params["status"] == "live"


@respx.mock
async def test_search_players():
    respx.get(f"{BASE}/players").mock(
        return_value=httpx.Response(200, json={"data": [{"name": "Alcaraz"}]})
    )
    client = make_client()
    data = await client.search_players("alcaraz")
    assert data[0]["name"] == "Alcaraz"


@respx.mock
async def test_rankings_sorted_and_sliced_client_side():
    payload = {
        "data": [
            {"name": "C", "ranking": 3},
            {"name": "A", "ranking": 1},
            {"name": "no-rank"},  # dropped: no ranking
            {"name": "B", "ranking": 2},
        ]
    }
    respx.get(f"{BASE}/players").mock(return_value=httpx.Response(200, json=payload))
    client = make_client()
    data = await client.rankings(limit=2)
    assert [p["name"] for p in data] == ["A", "B"]


@respx.mock
async def test_fixtures():
    respx.get(f"{BASE}/fixtures").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "f1"}]})
    )
    client = make_client()
    assert await client.fixtures() == [{"id": "f1"}]


@respx.mock
async def test_missing_data_key_returns_empty_list():
    respx.get(f"{BASE}/matches").mock(return_value=httpx.Response(200, json={}))
    client = make_client()
    assert await client.live_matches() == []


@respx.mock
async def test_401_raises_auth_error():
    respx.get(f"{BASE}/matches").mock(
        return_value=httpx.Response(401, json={"error": "unauthorized"})
    )
    client = make_client()
    with pytest.raises(AuthError):
        await client.live_matches()


@respx.mock
async def test_429_raises_rate_limit_error():
    respx.get(f"{BASE}/matches").mock(return_value=httpx.Response(429))
    client = make_client()
    with pytest.raises(RateLimitError):
        await client.live_matches()


@respx.mock
async def test_500_raises_api_error():
    respx.get(f"{BASE}/matches").mock(return_value=httpx.Response(500))
    client = make_client()
    with pytest.raises(ApiError):
        await client.live_matches()


@respx.mock
async def test_network_error_raises_api_error():
    respx.get(f"{BASE}/matches").mock(side_effect=httpx.ConnectError("boom"))
    client = make_client()
    with pytest.raises(ApiError):
        await client.live_matches()
