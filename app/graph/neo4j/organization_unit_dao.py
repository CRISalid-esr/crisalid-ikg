# pylint: disable=duplicate-code
from loguru import logger
from neo4j import AsyncSession

from app.errors.conflict_error import ConflictError
from app.errors.database_error import handle_database_errors
from app.errors.not_found_error import NotFoundError
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.neo4j_dao import Neo4jDAO
from app.graph.neo4j.utils import load_query
from app.models.identifier_types import OrganizationIdentifierType
from app.models.organization_unit import (
    AdministrativeUnit,
    Institution,
    InstitutionSubdivision,
    OrganizationBase,
    OrganizationUnit,
    ResearchUnit,
    SupportUnit,
    Team,
    UnitSubdivision,
    nonUnitAdapter,
    unitAdapter,
)
from app.services.identifiers.identifier_service import AgentIdentifierService


class OrganizationUnitDAO(Neo4jDAO):
    """
    Data access object for all research organization structures (OrganizationUnit nodes).
    """

    @handle_database_errors
    async def create(self, org_unit: OrganizationBase) -> OrganizationBase:
        """Create a new OrganizationUnit node in the graph."""
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                await session.write_transaction(
                    self._create_organization_unit_transaction, org_unit
                )
        return org_unit

    @handle_database_errors
    async def update(self, org_unit: OrganizationBase) -> OrganizationBase:
        """Update an existing OrganizationUnit node in the graph."""
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                await session.write_transaction(
                    self._update_organization_unit_transaction, org_unit
                )
        return org_unit

    @handle_database_errors
    async def create_or_update(self, org_unit: OrganizationBase) -> tuple[str, Neo4jDAO.Status]:
        """Create an OrganizationUnit if it does not exist, otherwise update it."""
        org_unit.uid = AgentIdentifierService.compute_uid_for(org_unit)
        existing = await self.find_by_identifier(
            OrganizationIdentifierType.LOCAL,
            org_unit.get_identifier(OrganizationIdentifierType.LOCAL).value,
        )
        if existing:
            async with Neo4jConnexion().get_driver() as driver:
                async with driver.session() as session:
                    await session.write_transaction(
                        self._update_organization_unit_transaction, org_unit
                    )
            return org_unit.uid, self.Status.UPDATED
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                await session.write_transaction(
                    self._create_organization_unit_transaction, org_unit
                )
        return org_unit.uid, self.Status.CREATED

    @handle_database_errors
    async def find_by_identifier(
        self,
        identifier_type: OrganizationIdentifierType,
        identifier_value: str,
    ) -> OrganizationUnit | None:
        """Find an OrganizationUnit by one of its identifiers."""
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    result = await tx.run(
                        load_query("find_organization_unit_by_identifier"),
                        identifier_type=identifier_type.value,
                        identifier_value=identifier_value,
                    )
                    record = await result.single()
                    if record:
                        return self._hydrate(record)
                    return None

    @handle_database_errors
    async def get(self, uid: str) -> OrganizationUnit | None:
        """Retrieve an OrganizationUnit by its uid."""
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                return await session.read_transaction(
                    self._get_organization_unit_by_uid, uid
                )

    @handle_database_errors
    async def get_all_uids(self) -> list[str]:
        """Return the uids of all OrganizationUnit nodes."""
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    result = await tx.run(load_query("get_all_organization_unit_uids"))
                    return [record["uid"] async for record in result]

    # ── Transaction helpers ────────────────────────────────────────────────────

    @classmethod
    async def _create_organization_unit_transaction(
        cls, tx: AsyncSession, org_unit: OrganizationBase
    ):
        org_unit.uid = AgentIdentifierService.compute_uid_for(org_unit)
        if await cls._organization_unit_uid_exists(org_unit.uid, tx):
            raise ConflictError(
                f"Organization unit with uid {org_unit.uid} already exists"
            )

        labels = cls._get_labels(org_unit)
        properties = cls._get_node_properties(org_unit)

        await tx.run(
            load_query("create_organization_unit"),
            labels=labels,
            properties=properties,
            short_labels=[sl.model_dump() for sl in org_unit.short_labels],
            long_labels=[ll.model_dump() for ll in org_unit.long_labels],
            local_types=[lt.model_dump() for lt in org_unit.local_types],
            descriptions=[
                {"key": d.key, "value": d.value, "language": d.language}
                for d in org_unit.descriptions
            ],
            identifiers=[i.dict() for i in org_unit.identifiers],
        )

        await cls._create_org_relationships(tx, org_unit)
        return org_unit

    @classmethod
    async def _update_organization_unit_transaction(
        cls, tx: AsyncSession, org_unit: OrganizationBase
    ):
        org_unit.uid = org_unit.uid or AgentIdentifierService.compute_uid_for(org_unit)
        if not await cls._organization_unit_uid_exists(org_unit.uid, tx):
            raise NotFoundError(
                f"Organization unit with uid {org_unit.uid} does not exist"
            )

        # Delete all label/description relationships (not the nodes)
        await tx.run(
            load_query("delete_organization_unit_labels"),
            uid=org_unit.uid,
        )
        # Delete identifier relationships not in the new set (preserves AgentIdentifier nodes)
        await tx.run(
            load_query("delete_organization_unit_identifiers"),
            uid=org_unit.uid,
            identifier_types=[i.type.value for i in org_unit.identifiers],
            identifier_values=[i.value for i in org_unit.identifiers],
        )
        # Delete all org-to-org relationships (MEMBER_OF / PART_OF to OrganizationUnit)
        await tx.run(
            load_query("delete_organization_unit_org_relationships"),
            uid=org_unit.uid,
        )

        # Recreate labels and identifiers
        await tx.run(
            load_query("create_organization_unit_labels"),
            uid=org_unit.uid,
            short_labels=[sl.model_dump() for sl in org_unit.short_labels],
            long_labels=[ll.model_dump() for ll in org_unit.long_labels],
            local_types=[lt.model_dump() for lt in org_unit.local_types],
            descriptions=[
                {"key": d.key, "value": d.value, "language": d.language}
                for d in org_unit.descriptions
            ],
        )
        await tx.run(
            load_query("create_organization_unit_identifiers"),
            uid=org_unit.uid,
            identifiers=[i.dict() for i in org_unit.identifiers],
        )

        await cls._create_org_relationships(tx, org_unit)
        return org_unit

    @classmethod
    async def _create_org_relationships(cls, tx: AsyncSession, org_unit: OrganizationBase):
        for parent in org_unit.parents:
            if not await cls._organization_unit_uid_exists(parent.target, tx):
                logger.error(
                    "Target {} not found for PART_OF relationship from {}",
                    parent.target,
                    org_unit.uid,
                )
                continue
            await tx.run(
                load_query("create_organization_unit_part_of"),
                uid=org_unit.uid,
                target_uid=parent.target,
                start_date=str(parent.start_date) if parent.start_date else None,
                end_date=str(parent.end_date) if parent.end_date else None,
            )

        for membership in org_unit.memberships:
            if not await cls._organization_unit_uid_exists(membership.target, tx):
                logger.error(
                    "Target {} not found for MEMBER_OF relationship from {}",
                    membership.target,
                    org_unit.uid,
                )
                continue
            await tx.run(
                load_query("create_organization_unit_member_of"),
                uid=org_unit.uid,
                target_uid=membership.target,
                position=membership.position.value if membership.position else None,
                start_date=str(membership.start_date) if membership.start_date else None,
                end_date=str(membership.end_date) if membership.end_date else None,
            )

    @staticmethod
    async def _organization_unit_uid_exists(uid: str, tx) -> bool:
        result = await tx.run(load_query("organization_unit_exists"), uid=uid)
        record = await result.single()
        return record is not None

    @classmethod
    async def _get_organization_unit_by_uid(cls, tx: AsyncSession, uid: str):
        result = await tx.run(
            load_query("find_organization_unit_by_uid"), uid=uid
        )
        record = await result.single()
        if record:
            return cls._hydrate(record)
        return None

    # ── Label / property helpers ───────────────────────────────────────────────

    @staticmethod
    def _get_labels(org_unit: OrganizationBase) -> list[str]:
        labels = ["OrganizationUnit"]
        if isinstance(org_unit, ResearchUnit):
            labels += ["Unit", "ResearchUnit"]
        elif isinstance(org_unit, SupportUnit):
            labels += ["Unit", "SupportUnit"]
        elif isinstance(org_unit, AdministrativeUnit):
            labels += ["Unit", "AdministrativeUnit"]
        elif isinstance(org_unit, Institution):
            labels.append("Institution")
        elif isinstance(org_unit, InstitutionSubdivision):
            labels.append("InstitutionSubdivision")
        elif isinstance(org_unit, UnitSubdivision):
            labels.append("UnitSubdivision")
        elif isinstance(org_unit, Team):
            labels.append("Team")
        return labels

    @staticmethod
    def _get_node_properties(org_unit: OrganizationBase) -> dict:
        props: dict = {
            "uid": org_unit.uid,
            "generic_type": org_unit.generic_type.value,
        }
        if org_unit.national_type:
            props["national_type"] = org_unit.national_type.value
        if hasattr(org_unit, "main_mission") and org_unit.main_mission:
            props["main_mission"] = org_unit.main_mission.value
        return props

    # ── Hydration ─────────────────────────────────────────────────────────────

    @staticmethod
    def _hydrate(record) -> OrganizationUnit:
        org_data = dict(record["o"])
        generic_type = org_data.get("generic_type")

        short_labels = [
            {"value": n["value"], "language": n.get("language", "und")}
            for n in record["short_labels"]
        ]
        long_labels = [
            {"value": n["value"], "language": n.get("language", "und")}
            for n in record["long_labels"]
        ]
        descriptions = [
            {"value": n["value"], "language": n.get("language", "und")}
            for n in record["descriptions"]
        ]
        local_types = [
            {"value": n["value"], "language": n.get("language", "und")}
            for n in record["local_types"]
        ]
        identifiers = [
            {"type": i["type"], "value": i["value"]}
            for i in record["identifiers"]
        ]

        memberships = []
        for m in record["memberships"]:
            if m is None or m.get("target_uid") is None:
                continue
            rel = dict(m.get("rel_props") or {})
            memberships.append({
                "target": m["target_uid"],
                "position": rel.get("position"),
                "start_date": str(rel["start_date"]) if rel.get("start_date") else None,
                "end_date": str(rel["end_date"]) if rel.get("end_date") else None,
            })

        parents = []
        for p in record["parents"]:
            if p is None or p.get("target_uid") is None:
                continue
            rel = dict(p.get("rel_props") or {})
            parents.append({
                "target": p["target_uid"],
                "start_date": str(rel["start_date"]) if rel.get("start_date") else None,
                "end_date": str(rel["end_date"]) if rel.get("end_date") else None,
            })

        data = {
            "uid": org_data["uid"],
            "generic_type": generic_type,
            "national_type": org_data.get("national_type"),
            "short_labels": short_labels,
            "long_labels": long_labels,
            "descriptions": descriptions,
            "local_types": local_types,
            "identifiers": identifiers,
            "memberships": memberships,
            "parents": parents,
        }

        if generic_type == "unit":
            data["main_mission"] = org_data.get("main_mission")
            return unitAdapter.validate_python(data)
        return nonUnitAdapter.validate_python(data)
