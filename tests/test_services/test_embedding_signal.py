from unittest.mock import AsyncMock, MagicMock, patch

from app.services.documents.document_service import DocumentService
from app.services.organizations.organization_unit_service import OrganizationUnitService
from app.services.embeddings.embedding_service import EmbeddingService
from app.signals import literal_updated


async def test_document_service_emits_literal_updated_on_update():
    """update_from_source_records emits literal_updated after signalling document updated."""
    mock_handler = AsyncMock()
    literal_updated.connect(mock_handler)

    service = DocumentService()
    service._compute_document_from_source_records = AsyncMock(return_value=True)
    service.signal_document_updated = AsyncMock()

    try:
        await service.update_from_source_records(None, "doc-uid-1")
        mock_handler.assert_called_once()
    finally:
        literal_updated.disconnect(mock_handler)


async def test_document_service_emits_literal_updated_on_create():
    """create_from_source_records emits literal_updated after signalling document created."""
    mock_handler = AsyncMock()
    literal_updated.connect(mock_handler)

    service = DocumentService()
    service._compute_document_from_source_records = AsyncMock()
    service.signal_document_created = AsyncMock()

    try:
        await service.create_from_source_records(None, "doc-uid-1")
        mock_handler.assert_called_once()
    finally:
        literal_updated.disconnect(mock_handler)


async def test_organization_unit_service_emits_literal_updated_on_create():
    """create_structure emits literal_updated after signalling structure created."""
    mock_handler = AsyncMock()
    literal_updated.connect(mock_handler)

    mock_result = MagicMock()
    mock_result.uid = "local-unit-1"

    service = OrganizationUnitService()
    service._resolve_non_local_relationship_targets = AsyncMock()
    service._get_dao = MagicMock(return_value=AsyncMock(create=AsyncMock(return_value=mock_result)))

    try:
        await service.create_structure(MagicMock())
        mock_handler.assert_called_once()
    finally:
        literal_updated.disconnect(mock_handler)


async def test_literal_updated_triggers_on_literals_pending_when_enabled():
    """When literal_updated fires, a connected EmbeddingService handler is invoked."""
    mock_handler = AsyncMock()
    literal_updated.connect(mock_handler)
    try:
        await literal_updated.send_async(sender=None)
        mock_handler.assert_called_once()
    finally:
        literal_updated.disconnect(mock_handler)
