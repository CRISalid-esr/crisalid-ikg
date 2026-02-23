import inflection
from neo4j import AsyncManagedTransaction

from app.errors.conflict_error import ConflictError
from app.errors.database_error import handle_database_errors
from app.errors.not_found_error import NotFoundError
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.neo4j_dao import Neo4jDAO
from app.graph.neo4j.utils import load_query
from app.models.source_organization_identifiers import SourceOrganizationIdentifier
from app.models.source_organizations import SourceOrganization


class SourceOrganizationDAO(Neo4jDAO):
    """
    Data access object for source people and the neo4j database
    """

    @handle_database_errors
    async def create(self, source_organization: SourceOrganization
                     ) -> SourceOrganization:
        """
        Create  a source organization in the graph database

        :param source_organization: source organization Pydantic object
        :return: source organization object
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                await session.write_transaction(self._create_source_organization_transaction,
                                                source_organization
                                                )
        return source_organization

    @handle_database_errors
    async def update(self, source_organization: SourceOrganization) -> SourceOrganization:
        """
        Update a source organization in the graph database

        :param source_organization: source organization Pydantic object
        :return: source organization object
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    source_organization_exists = \
                        await SourceOrganizationDAO._source_organization_exists(
                            tx,
                            source_organization.uid)
                    if not source_organization_exists:
                        raise ValueError(
                            f"Source organization with uid {source_organization.uid} not found")
                    await self._update_source_organization_transaction(tx,
                                                                       source_organization)
                    return source_organization

    @handle_database_errors
    async def source_organization_exists(self, source_organization_uid: str) -> bool:
        """
        Check if a source organization exists in the graph database

        :param source_organization_uid: source organization uid
        :return: True if the source organization exists, False otherwise
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    return await SourceOrganizationDAO._source_organization_exists(
                        tx,
                        source_organization_uid)

    @handle_database_errors
    async def get_by_uid(self, source_organization_uid: str) -> SourceOrganization:
        """
        Get a source organization from the graph database

        :param source_organization_uid: source organization uid
        :return: source organization object
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    return await SourceOrganizationDAO._get_source_organization_by_uid(
                        tx,
                        source_organization_uid)

    @staticmethod
    async def _source_organization_exists(tx: AsyncManagedTransaction,
                                          source_organization_uid: str) -> bool:
        result = await tx.run(
            load_query("source_organization_exists"),
            source_organization_uid=source_organization_uid
        )
        organization = await result.single()
        return organization is not None

    @classmethod
    async def _get_source_organization_by_uid(cls,
                                              tx: AsyncManagedTransaction,
                                              source_organization_uid: str
                                              ) -> SourceOrganization | None:
        result = await tx.run(
            load_query("get_source_organization_by_uid"),
            uid=source_organization_uid
        )
        source_organization = await result.single()
        if source_organization:
            return cls._hydrate(source_organization)
        return None

    @classmethod
    async def _create_source_organization_transaction(cls, tx: AsyncManagedTransaction,
                                                      source_organization: SourceOrganization
                                                      ):
        source_organization_exists = await SourceOrganizationDAO._source_organization_exists(
            tx,
            source_organization.uid)
        if source_organization_exists:
            raise ConflictError(
                f"Source organization with uid {source_organization.uid} already exists")
        create_source_organization_query = load_query("create_source_organization")
        create_source_organization_query = cls._replace_dynamic_label(
            create_source_organization_query,
            source_organization.type)
        await tx.run(
            create_source_organization_query,
            source_organization_uid=source_organization.uid,
            source=source_organization.source.value,
            source_identifier=source_organization.source_identifier,
            name=source_organization.name,
            type=source_organization.type.value,
            identifiers=[identifier.model_dump() for identifier in source_organization.identifiers],
        )

    @classmethod
    async def _update_source_organization_transaction(
            cls,
            tx: AsyncManagedTransaction,
            source_organization: SourceOrganization
    ):
        source_organization_exists = await SourceOrganizationDAO._source_organization_exists(
            tx, source_organization.uid
        )
        if not source_organization_exists:
            raise NotFoundError(
                f"Source organization with uid {source_organization.uid} does not exist"
            )
        update_source_organization_query = load_query("update_source_organization")
        update_source_organization_query = cls._replace_dynamic_label(
            update_source_organization_query,
            source_organization.type
        )

        await tx.run(
            update_source_organization_query,
            source_organization_uid=source_organization.uid,
            source=source_organization.source.value,
            source_identifier=source_organization.source_identifier,
            name=source_organization.name,
            type=source_organization.type.value,
            identifiers=[identifier.model_dump() for identifier in source_organization.identifiers],
            identifier_composite_keys=[
                f"{identifier.type}:{identifier.value}" for identifier in
                source_organization.identifiers
            ],
        )

    @handle_database_errors
    async def create_source_organization_cluster(
            self,
            source_organization_uid: str,
    ) -> list[SourceOrganization]:
        """
        Return the cluster of SourceOrganizations connected by identifiers
        starting from the given source organization uid.
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    exists = await SourceOrganizationDAO._source_organization_exists(
                        tx, source_organization_uid
                    )
                    if not exists:
                        raise NotFoundError(
                            f"Source organization with uid {source_organization_uid} not found"
                        )

                    return await SourceOrganizationDAO._create_source_organization_cluster_tx(
                        tx, source_organization_uid
                    )

    @classmethod
    async def _create_source_organization_cluster_tx(
            cls,
            tx: AsyncManagedTransaction,
            source_organization_uid: str,
    ) -> list[SourceOrganization]:
        result = await tx.run(
            load_query("create_source_organizations_cluster"),
            source_organization_uid=source_organization_uid,
        )

        records = await result.data()
        return [cls._hydrate(r) for r in records]

    @staticmethod
    def _hydrate(record) -> SourceOrganization:
        if record["s"]["type"]:
            organization_type = record["s"]["type"].upper()
        else:
            organization_type = "ORGANIZATION"
        assert organization_type in SourceOrganization.SourceOrganisationType.__members__
        source_organization = SourceOrganization(
            uid=record["s"]["uid"],
            source=record["s"]["source"],
            source_identifier=record["s"]["source_identifier"],
            name=record["s"]["name"],
            type=SourceOrganization.SourceOrganisationType[organization_type],
            identifiers=[]
        )
        for identifier in record["identifiers"]:
            # continue if type or value is None
            if identifier["type"] is None or identifier["value"] is None:
                continue
            source_organization.identifiers.append(
                SourceOrganizationIdentifier(**identifier))
        return source_organization

    @staticmethod
    def _replace_dynamic_label(query: str,
                               organization_type: SourceOrganization.SourceOrganisationType) -> str:
        if organization_type is None:
            dynamic_label = ""  # no colon needed; it's already in the template
        else:
            dynamic_label = f":Source{inflection.camelize(organization_type.value)}"
        return query.replace(":${dynamicLabel}", dynamic_label)
