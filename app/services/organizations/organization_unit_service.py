from typing import cast

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao import DAO
from app.graph.neo4j.organization_unit_dao import OrganizationUnitDAO
from app.models.organization_unit import OrganizationBase, OrganizationUnit
from app.signals import structure_created, structure_updated, structure_unchanged, structure_deleted


class OrganizationUnitService:
    """Service for all research organization structure types."""

    async def signal_structure_created(self, uid: str):
        """Dispatch the 'created' signal for a structure."""
        await structure_created.send_async(self, payload=uid)

    async def signal_structure_updated(self, uid: str):
        """Dispatch the 'updated' signal for a structure."""
        await structure_updated.send_async(self, payload=uid)

    async def signal_structure_unchanged(self, uid: str):
        """Dispatch the 'unchanged' signal for a structure."""
        await structure_unchanged.send_async(self, payload=uid)

    async def signal_structure_deleted(self, uid: str):
        """Dispatch the 'deleted' signal for a structure."""
        await structure_deleted.send_async(self, payload=uid)

    async def create_structure(self, org_unit: OrganizationBase) -> OrganizationBase:
        """Persist a new structure and emit the created signal."""
        result = await self._get_dao().create(org_unit)
        await structure_created.send_async(self, payload=result.uid)
        return result

    async def update_structure(self, org_unit: OrganizationBase) -> OrganizationBase:
        """Update an existing structure and emit the updated signal."""
        result = await self._get_dao().update(org_unit)
        await structure_updated.send_async(self, payload=result.uid)
        return result

    async def create_or_update_structure(self, org_unit: OrganizationBase) -> OrganizationBase:
        """Create or update a structure and emit the appropriate signal."""
        uid, status = await self._get_dao().create_or_update(org_unit)
        if status == DAO.Status.CREATED:
            await structure_created.send_async(self, payload=uid)
        elif status == DAO.Status.UPDATED:
            await structure_updated.send_async(self, payload=uid)
        return org_unit

    async def get_structure_by_uid(self, uid: str) -> OrganizationUnit | None:
        """Retrieve a structure by its uid."""
        return await self._get_dao().get(uid)

    async def get_all_structure_uids(self) -> list[str]:
        """Return the uids of all persisted structures."""
        return await self._get_dao().get_all_uids()

    @staticmethod
    def _get_dao() -> OrganizationUnitDAO:
        settings = get_app_settings()
        return cast(
            OrganizationUnitDAO,
            AbstractDAOFactory()
            .get_dao_factory(settings.graph_db)
            .get_dao(OrganizationBase),
        )
