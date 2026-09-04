import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from app.services.documents.crisalid_taxi_client import CrisalidTaxiClient

FAKE_RESPONSE = {
    "generated_at": "20260615T113123Z",
    "model": "bge-m3",
    "query_count": 1,
    "total_matches": 2,
    "results": [
        {"id": "doc-1", "matches": [
            {"concept_uid": "https://openalex.org/T1", "rel_type": "HAS_TOPIC", "value": 0.77},
            {"concept_uid": "https://openalex.org/subfields/1", "rel_type": "HAS_SUBFIELD",
             "value": 0.61},
        ]},
    ],
}


def make_settings(url="http://taxi.test", timeout=12, threshold=0.6, max_failures=3,
                  open_seconds=300):
    settings = MagicMock()
    settings.app_env = "TEST"
    settings.taxi_api_url = url
    settings.taxi_timeout_seconds = timeout
    settings.taxi_similarity_threshold = threshold
    settings.taxi_max_consecutive_failures = max_failures
    settings.taxi_circuit_open_seconds = open_seconds
    return settings


def make_mock_session(response_body=None, status=200, post_side_effect=None):
    mock_resp = AsyncMock()
    mock_resp.status = status
    mock_resp.json = AsyncMock(return_value=response_body)
    mock_resp.text = AsyncMock(return_value='{"detail": "boom"}')

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_resp
    mock_ctx.__aexit__.return_value = None

    mock_session = MagicMock()
    if post_side_effect is not None:
        mock_session.post.side_effect = post_side_effect
    else:
        mock_session.post.return_value = mock_ctx

    mock_session_ctx = MagicMock()
    mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_ctx.__aexit__ = AsyncMock(return_value=None)
    return mock_session_ctx, mock_session


@pytest.fixture(autouse=True)
def _reset_breaker():
    CrisalidTaxiClient.reset()
    yield
    CrisalidTaxiClient.reset()


@pytest.fixture(name="mock_taxi_client")
def fixture_disable_global_taxi_mock():
    """Disable the autouse mock of CrisalidTaxiClient.match for this module."""
    yield None


def _client(settings=None):
    with patch("app.services.documents.crisalid_taxi_client.get_app_settings",
               return_value=settings or make_settings()):
        return CrisalidTaxiClient()


def test_init_raises_without_api_url():
    with pytest.raises(ValueError, match="TAXI_API_URL"):
        _client(make_settings(url=""))


async def test_match_sends_payload_with_threshold_and_uses_timeout():
    client = _client(make_settings(timeout=42, threshold=0.55))
    session_ctx, session = make_mock_session(FAKE_RESPONSE)
    with patch("aiohttp.ClientSession", return_value=session_ctx) as session_cls:
        response = await client.match([{"id": "doc-1", "text": "some text"}])

    assert session_cls.call_args[1]["timeout"].total == 42
    url, kwargs = session.post.call_args[0][0], session.post.call_args[1]
    assert url == "http://taxi.test/api/v1/match/"
    assert kwargs["json"] == {"inputs": [{"id": "doc-1", "text": "some text"}],
                              "similarity_threshold": 0.55}
    assert response.model == "bge-m3"
    assert [m.rel_type for m in response.results["doc-1"]] == ["HAS_TOPIC", "HAS_SUBFIELD"]
    assert response.results["doc-1"][0].value == pytest.approx(0.77)


async def test_match_returns_none_on_http_error():
    client = _client()
    session_ctx, _ = make_mock_session({"detail": "boom"}, status=500)
    with patch("aiohttp.ClientSession", return_value=session_ctx):
        assert await client.match([{"id": "doc-1", "text": "t"}]) is None
    assert not CrisalidTaxiClient.is_open()


async def test_match_returns_none_on_timeout_and_malformed_body():
    client = _client()
    session_ctx, _ = make_mock_session(post_side_effect=asyncio.TimeoutError())
    with patch("aiohttp.ClientSession", return_value=session_ctx):
        assert await client.match([{"id": "doc-1", "text": "t"}]) is None
    session_ctx, _ = make_mock_session(post_side_effect=aiohttp.ClientConnectionError("down"))
    with patch("aiohttp.ClientSession", return_value=session_ctx):
        assert await client.match([{"id": "doc-1", "text": "t"}]) is None
    session_ctx, _ = make_mock_session({"unexpected": True})
    with patch("aiohttp.ClientSession", return_value=session_ctx):
        assert await client.match([{"id": "doc-1", "text": "t"}]) is None


async def test_circuit_opens_after_consecutive_failures_and_recovers():
    client = _client(make_settings(max_failures=3, open_seconds=300))
    failing_ctx, _ = make_mock_session(status=503)
    with patch("aiohttp.ClientSession", return_value=failing_ctx) as session_cls:
        for _ in range(3):
            await client.match([{"id": "doc-1", "text": "t"}])
        assert CrisalidTaxiClient.is_open()
        assert session_cls.call_count == 3
        # while open, no HTTP call at all
        assert await client.match([{"id": "doc-1", "text": "t"}]) is None
        assert session_cls.call_count == 3

    ok_ctx, _ = make_mock_session(FAKE_RESPONSE)
    with patch("time.monotonic", return_value=CrisalidTaxiClient._open_until + 1):  # pylint: disable=protected-access
        assert not CrisalidTaxiClient.is_open()
        with patch("aiohttp.ClientSession", return_value=ok_ctx):
            assert await client.match([{"id": "doc-1", "text": "t"}]) is not None
    assert not CrisalidTaxiClient.is_open()
    assert CrisalidTaxiClient._consecutive_failures == 0  # pylint: disable=protected-access


async def test_success_resets_failure_counter():
    client = _client(make_settings(max_failures=3))
    failing_ctx, _ = make_mock_session(status=500)
    ok_ctx, _ = make_mock_session(FAKE_RESPONSE)
    with patch("aiohttp.ClientSession", return_value=failing_ctx):
        await client.match([{"id": "doc-1", "text": "t"}])
        await client.match([{"id": "doc-1", "text": "t"}])
    with patch("aiohttp.ClientSession", return_value=ok_ctx):
        await client.match([{"id": "doc-1", "text": "t"}])
    with patch("aiohttp.ClientSession", return_value=failing_ctx):
        await client.match([{"id": "doc-1", "text": "t"}])
        await client.match([{"id": "doc-1", "text": "t"}])
    assert not CrisalidTaxiClient.is_open()
