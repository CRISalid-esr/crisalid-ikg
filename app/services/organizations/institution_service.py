from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.utils import load_query
from app.models.identifier_types import OrganizationIdentifierType
from app.models.organization_unit import Institution, OrganizationBase
from app.services.identifiers.identifier_service import AgentIdentifierService
from app.services.organizations.institution_registry_service import InstitutionRegistryService
from app.amqp.message_mode import MessageMode
from app.signals import structure_created


class InstitutionService:
    """
    Service to handle operations on institutions in the graph database.
    """

    async def institution_uid(self, entity_uid: str) -> str | None:
        """
        Return the uid if an Institution node with this uid exists, else None.
        Matches both old-style (:Institution) and new-style (:OrganizationUnit:Institution) nodes.
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    result = await tx.run(
                        load_query("institution_uid_by_uid"),
                        uid=entity_uid,
                    )
                    record = await result.single()
                    return record["uid"] if record else None

    async def resolve_institution_uid(self, entity_uid: str) -> str | None:
        """
        Resolve an entity uid to the uid of an existing Institution node.
        First tries an exact uid match, then parses the uid as an identifier
        "<type>-<value>" (e.g. "uai-12345") and matches it against the
        HAS_IDENTIFIER edges of Institution nodes, preferring internal ones.
        Returns None if nothing matches.
        """
        existing_uid = await self.institution_uid(entity_uid)
        if existing_uid is not None:
            return existing_uid
        separator = AgentIdentifierService.IDENTIFIER_SEPARATOR
        if separator not in entity_uid:
            return None
        identifier_type, identifier_value = entity_uid.split(separator, 1)
        if OrganizationIdentifierType.from_str(identifier_type) is None:
            return None
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    result = await tx.run(
                        load_query("institution_uid_by_identifier"),
                        identifier_type=identifier_type,
                        identifier_value=identifier_value,
                    )
                    record = await result.single()
                    return record["uid"] if record else None

    async def create_institution(self, entity_uid: str) -> str:
        """
        Fetch institution data from external registry and persist it.
        Returns the institution uid.
        """
        identifier = AgentIdentifierService.compute_identifier_from_uid(
            Institution, entity_uid
        )
        registry_service = InstitutionRegistryService()
        institution = await registry_service.fetch_institution_from_external_source(
            [identifier]
        )
        if institution is None:
            raise ValueError(
                f"No institution found from external source for entity_uid {entity_uid!r}"
            )
        dao = self._get_org_unit_dao()
        await dao.create(institution)
        await structure_created.send_async(self, payload=institution.uid, mode=MessageMode.BATCH)
        return institution.uid

    async def get_institution_by_uid(self, uid: str) -> Institution | None:
        """Retrieve an institution by its uid."""
        return await self._get_org_unit_dao().get(uid)

    @staticmethod
    def _get_org_unit_dao():
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db).get_dao(OrganizationBase)
