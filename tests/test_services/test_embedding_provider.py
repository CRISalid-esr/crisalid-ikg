import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.embeddings.providers.openai_compatible import OpenAICompatibleProvider

FAKE_RESPONSE = {
    "data": [
        {"index": 0, "embedding": [0.1, 0.2, 0.3]},
        {"index": 1, "embedding": [0.4, 0.5, 0.6]},
    ]
}


def make_settings(url="http://embed.test", model="emb-model", key="secret", timeout=10):
    s = MagicMock()
    s.embedding_api_url = url
    s.embedding_api_model = model
    s.embedding_api_key = key
    s.embedding_timeout_seconds = timeout
    return s


def make_mock_session(response_body, status=200):
    mock_resp = AsyncMock()
    mock_resp.status = status
    mock_resp.json = AsyncMock(return_value=response_body)
    mock_resp.raise_for_status = MagicMock()

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_resp
    mock_ctx.__aexit__.return_value = None

    mock_session = MagicMock()
    mock_session.post.return_value = mock_ctx

    mock_session_ctx = MagicMock()
    mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_ctx.__aexit__ = AsyncMock(return_value=None)
    return mock_session_ctx, mock_session


def test_init_raises_without_api_url():
    settings = make_settings(url="")
    with pytest.raises(ValueError, match="EMBEDDING_API_URL"):
        OpenAICompatibleProvider(settings)


def test_init_raises_without_api_model():
    settings = make_settings(model="")
    with pytest.raises(ValueError, match="EMBEDDING_API_MODEL"):
        OpenAICompatibleProvider(settings)


async def test_embed_texts_returns_correct_vectors():
    settings = make_settings()
    provider = OpenAICompatibleProvider(settings)
    mock_session_ctx, _ = make_mock_session(FAKE_RESPONSE)

    with patch("aiohttp.ClientSession", return_value=mock_session_ctx):
        result = await provider.embed_texts(["text_a", "text_b"])

    assert result == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]


async def test_embed_texts_sends_correct_payload():
    settings = make_settings()
    provider = OpenAICompatibleProvider(settings)
    mock_session_ctx, mock_session = make_mock_session(FAKE_RESPONSE)

    with patch("aiohttp.ClientSession", return_value=mock_session_ctx):
        await provider.embed_texts(["text_a", "text_b"])

    call_kwargs = mock_session.post.call_args
    assert call_kwargs[0][0].endswith("/v1/embeddings")
    assert call_kwargs[1]["json"] == {"model": "emb-model", "input": ["text_a", "text_b"]}


async def test_embed_texts_includes_auth_header_when_key_set():
    settings = make_settings(key="secret")
    provider = OpenAICompatibleProvider(settings)
    single_response = {"data": [{"index": 0, "embedding": [0.1, 0.2, 0.3]}]}
    mock_session_ctx, mock_session = make_mock_session(single_response)

    with patch("aiohttp.ClientSession", return_value=mock_session_ctx):
        await provider.embed_texts(["text"])

    headers = mock_session.post.call_args[1]["headers"]
    assert headers.get("Authorization") == "Bearer secret"


async def test_embed_texts_no_auth_header_without_key():
    settings = make_settings(key="")
    provider = OpenAICompatibleProvider(settings)
    response = {"data": [{"index": 0, "embedding": [0.1]}]}
    mock_session_ctx, mock_session = make_mock_session(response)

    with patch("aiohttp.ClientSession", return_value=mock_session_ctx):
        await provider.embed_texts(["text"])

    headers = mock_session.post.call_args[1]["headers"]
    assert "Authorization" not in headers


async def test_embed_texts_sorts_out_of_order_response():
    settings = make_settings()
    provider = OpenAICompatibleProvider(settings)
    reversed_response = {
        "data": [
            {"index": 1, "embedding": [0.4, 0.5, 0.6]},
            {"index": 0, "embedding": [0.1, 0.2, 0.3]},
        ]
    }
    mock_session_ctx, _ = make_mock_session(reversed_response)

    with patch("aiohttp.ClientSession", return_value=mock_session_ctx):
        result = await provider.embed_texts(["first", "second"])

    assert result == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]


async def test_embed_texts_raises_on_count_mismatch():
    settings = make_settings()
    provider = OpenAICompatibleProvider(settings)
    one_embedding = {"data": [{"index": 0, "embedding": [0.1]}]}
    mock_session_ctx, _ = make_mock_session(one_embedding)

    with patch("aiohttp.ClientSession", return_value=mock_session_ctx):
        with pytest.raises(ValueError, match="2 texts"):
            await provider.embed_texts(["text_a", "text_b"])
