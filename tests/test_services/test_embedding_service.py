import hashlib
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.embeddings.embedding_service import EmbeddingService


def make_settings(enabled=True, model="test-model", batch_size=2):
    s = MagicMock()
    s.embedding_enabled = enabled
    s.embedding_api_model = model
    s.embedding_batch_size = batch_size
    return s


def make_node(element_id, value, embedding=None, embedding_hash=None, embedding_model=None):
    return {
        "element_id": element_id,
        "value": value,
        "embedding": embedding,
        "embedding_hash": embedding_hash,
        "embedding_model": embedding_model,
    }


def _sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@contextmanager
def _patched_service(settings, mock_dao, mock_provider):
    """Yield a patched EmbeddingService while keeping all patches active."""
    with patch("app.services.embeddings.embedding_service.get_app_settings",
               return_value=settings), \
         patch("app.services.embeddings.embedding_service.EmbeddableDAO",
               return_value=mock_dao), \
         patch("app.services.embeddings.embedding_service.get_embedding_provider",
               return_value=mock_provider):
        yield EmbeddingService()


async def test_on_literals_pending_disabled():
    settings = make_settings(enabled=False)
    mock_dao = AsyncMock()
    with _patched_service(settings, mock_dao, AsyncMock()) as service:
        await service.on_literals_pending(None)

    mock_dao.get_pending_nodes.assert_not_called()


async def test_on_literals_pending_enabled_processes_pending():
    settings = make_settings(enabled=True)
    mock_dao = AsyncMock()
    node_a = make_node("id-1", "hello")
    mock_dao.get_pending_nodes.side_effect = [[node_a], []]
    mock_provider = AsyncMock()
    mock_provider.embed_texts = AsyncMock(return_value=[[0.1, 0.2]])

    with _patched_service(settings, mock_dao, mock_provider) as service:
        await service.on_literals_pending(None)

    mock_dao.update_embeddings_batch.assert_called_once()


async def test_embed_batch_skips_already_valid_nodes():
    model = "test-model"
    value = "my text"
    settings = make_settings(model=model)
    mock_dao = AsyncMock()
    mock_provider = AsyncMock()

    node = make_node("id-1", value, embedding=[0.1], embedding_hash=_sha256(value),
                     embedding_model=model)
    with _patched_service(settings, mock_dao, mock_provider) as service:
        await service._embed_batch([node], mock_provider)

    mock_provider.embed_texts.assert_not_called()
    mock_dao.update_embeddings_batch.assert_called_once()
    rows = mock_dao.update_embeddings_batch.call_args[0][0]
    assert len(rows) == 1
    assert rows[0]["element_id"] == "id-1"
    assert rows[0]["embedding"] == [0.1]


async def test_embed_batch_calls_provider_for_pending_node():
    settings = make_settings(model="test-model")
    mock_dao = AsyncMock()
    mock_provider = AsyncMock()
    mock_provider.embed_texts = AsyncMock(return_value=[[0.5, 0.6]])

    node = make_node("id-1", "embed me")
    with _patched_service(settings, mock_dao, mock_provider) as service:
        await service._embed_batch([node], mock_provider)

    mock_provider.embed_texts.assert_called_once_with(["embed me"])
    mock_dao.update_embeddings_batch.assert_called_once()
    rows = mock_dao.update_embeddings_batch.call_args[0][0]
    assert rows[0]["element_id"] == "id-1"
    assert rows[0]["embedding"] == [0.5, 0.6]


async def test_embed_batch_marks_all_failed_on_provider_exception():
    settings = make_settings(model="test-model")
    mock_dao = AsyncMock()
    mock_provider = AsyncMock()
    mock_provider.embed_texts = AsyncMock(side_effect=RuntimeError("timeout"))

    node_a = make_node("id-1", "text a")
    node_b = make_node("id-2", "text b")
    with _patched_service(settings, mock_dao, mock_provider) as service:
        await service._embed_batch([node_a, node_b], mock_provider)

    assert mock_dao.mark_failed.call_count == 2
    calls = {c.args[0] for c in mock_dao.mark_failed.call_args_list}
    assert calls == {"id-1", "id-2"}
    mock_dao.update_embeddings_batch.assert_not_called()


async def test_embed_batch_mixed_valid_and_pending():
    model = "test-model"
    value_a = "valid text"
    settings = make_settings(model=model)
    mock_dao = AsyncMock()
    mock_provider = AsyncMock()
    mock_provider.embed_texts = AsyncMock(return_value=[[0.9]])

    node_a = make_node("id-1", value_a, embedding=[0.1], embedding_hash=_sha256(value_a),
                       embedding_model=model)
    node_b = make_node("id-2", "pending text")
    with _patched_service(settings, mock_dao, mock_provider) as service:
        await service._embed_batch([node_a, node_b], mock_provider)

    mock_provider.embed_texts.assert_called_once_with(["pending text"])
    assert mock_dao.update_embeddings_batch.call_count == 2


async def test_compute_embeddings_paginates_until_empty():
    settings = make_settings(model="test-model", batch_size=1)
    mock_dao = AsyncMock()
    node = make_node("id-1", "text")
    mock_dao.get_pending_nodes.side_effect = [[node], [node], []]
    mock_provider = AsyncMock()
    mock_provider.embed_texts = AsyncMock(return_value=[[0.1]])

    with _patched_service(settings, mock_dao, mock_provider) as service:
        await service.compute_embeddings(statuses=["pending"])

    assert mock_dao.get_pending_nodes.call_count == 3


async def test_compute_embeddings_type_filter_passed_to_dao():
    settings = make_settings()
    mock_dao = AsyncMock()
    mock_dao.get_pending_nodes.return_value = []

    with _patched_service(settings, mock_dao, AsyncMock()) as service:
        await service.compute_embeddings(statuses=["pending"], types=["document_title"])

    mock_dao.get_pending_nodes.assert_called_once()
    kwargs = mock_dao.get_pending_nodes.call_args.kwargs
    assert kwargs.get("types") == ["document_title"]


async def test_compute_embeddings_model_exclude_passed_to_dao():
    settings = make_settings()
    mock_dao = AsyncMock()
    mock_dao.get_pending_nodes.return_value = []

    with _patched_service(settings, mock_dao, AsyncMock()) as service:
        await service.compute_embeddings(statuses=["pending"], model_exclude="old-model")

    mock_dao.get_pending_nodes.assert_called_once()
    kwargs = mock_dao.get_pending_nodes.call_args.kwargs
    assert kwargs.get("model_exclude") == "old-model"
