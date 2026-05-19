from typing import cast

from loguru import logger

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao import DAO
from app.graph.neo4j.organization_unit_dao import OrganizationUnitDAO
from app.models.organization_unit import OrganizationBase, OrganizationUnit
from app.services.organizations.institution_service import InstitutionService
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
        await self._resolve_non_local_relationship_targets(org_unit)
        result = await self._get_dao().create(org_unit)
        await structure_created.send_async(self, payload=result.uid)
        return result

    async def update_structure(self, org_unit: OrganizationBase) -> OrganizationBase:
        """Update an existing structure and emit the updated signal."""
        await self._resolve_non_local_relationship_targets(org_unit)
        result = await self._get_dao().update(org_unit)
        await structure_updated.send_async(self, payload=result.uid)
        return result

    async def create_or_update_structure(self, org_unit: OrganizationBase) -> OrganizationBase:
        """Create or update a structure and emit the appropriate signal."""
        await self._resolve_non_local_relationship_targets(org_unit)
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

    async def _resolve_non_local_relationship_targets(self, org_unit: OrganizationBase):
        """
        For each non-local relationship target, ensure the institution exists in the graph.
        Non-local targets (uai-xxx, ror-xxx…) may be auto-created from the registry.
        Local targets (local-xxx) must have been created by a prior message; if missing,
        the DAO logs an error and silently skips the relationship.
        """
        all_targets = (
            {m.target for m in org_unit.memberships} |
            {p.target for p in org_unit.parents}
        )
        institution_service = InstitutionService()
        for target_uid in all_targets:
            if target_uid.startswith("local-"):
                continue
            existing = await self.get_structure_by_uid(target_uid)
            if existing is None:
                try:
                    await institution_service.create_institution(target_uid)
                    logger.info(
                        "Created institution {} from registry for relationship target",
                        target_uid,
                    )
                except (ValueError, Exception) as e:  # pylint: disable=broad-except
                    logger.warning(
                        "Could not resolve non-local relationship target {}: {}",
                        target_uid,
                        e,
                    )

    @staticmethod
    def _get_dao() -> OrganizationUnitDAO:
        settings = get_app_settings()
        return cast(
            OrganizationUnitDAO,
            AbstractDAOFactory()
            .get_dao_factory(settings.graph_db)
            .get_dao(OrganizationBase),
        )
