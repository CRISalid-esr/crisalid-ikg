from __future__ import annotations

import hashlib
import re

from neo4j import AsyncSession, AsyncManagedTransaction

from app.errors.conflict_error import ConflictError
from app.errors.database_error import handle_database_errors
from app.errors.not_found_error import NotFoundError
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.neo4j_dao import Neo4jDAO
from app.graph.neo4j.utils import load_query
from app.models.agent_identifiers import OrganizationIdentifier
from app.models.authority_organization_root import AuthorityOrganizationRoot
from app.models.authority_organization_state import AuthorityOrganizationState
from app.models.identifier_types import OrganizationIdentifierType
from app.models.literal import Literal
from app.models.places import Place
from app.models.source_organizations import SourceOrganization  # for enum
from app.models.structured_physical_address import StructuredPhysicalAddress


class AuthorityOrganizationDAO(Neo4jDAO):
    """
    DAO for AuthorityOrganization entities (states or roots)
    """

    @handle_database_errors
    async def get_states_with_compatible_identifiers(
            self,
            identifiers: list[OrganizationIdentifier],
    ) -> list[AuthorityOrganizationState]:
        """
        Retrieve AuthorityOrganizationStates that have at least one identifier
        compatible with the provided list and no conflicting identifiers.
        :param identifiers:
        :return:
        """
        if not identifiers:
            return []

        payload = [{"type": i.type.value, "value": i.value} for i in identifiers]

        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    result = await tx.run(
                        load_query("get_authority_organization_states_with_compatible_identifiers"),
                        identifiers=payload,
                    )
                    records = await result.data()
                    return [self._hydrate_authority_organization_state(r) for r in records]

    @handle_database_errors
    async def get_states_by_normalized_name(
            self,
            normalized_name: str,
    ) -> list[AuthorityOrganizationState]:
        """
        Retrieve AuthorityOrganizationStates by their normalized name.
        :param normalized_name:
        :return:
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    result = await tx.run(
                        load_query("get_authority_organization_states_by_normalized_name"),
                        normalized_name=normalized_name,
                    )
                    records = await result.data()
                    return [self._hydrate_authority_organization_state(r) for r in records]

    @handle_database_errors
    async def create_authority_organization_state(
            self,
            state: AuthorityOrganizationState
    ) -> AuthorityOrganizationState:
        """
        Create a new AuthorityOrganizationState in the database.
        :param state:
        :return:
        """
        # will be applied only in case of new state creation
        state.random_uid()
        new_state_uid = None
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                new_state_uid = await session.write_transaction(
                    self._create_authority_organization_state_tx,
                    state)

        return await self.get_authority_organization_state_by_uid(new_state_uid)

    @handle_database_errors
    async def update_authority_organization_state(
            self,
            state: AuthorityOrganizationState) -> AuthorityOrganizationState:
        """
        Update an existing AuthorityOrganizationState in the database.
        :param state:
        :return:
        """
        if not state.uid:
            raise ValueError("AuthorityOrganizationState.uid is required to update")

        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                await session.write_transaction(
                    self._update_authority_organization_state_tx,
                    state
                )

        return state

    @classmethod
    async def _create_authority_organization_state_tx(cls, tx: AsyncSession,
                                                      state: AuthorityOrganizationState) -> str:
        exists_result = await tx.run(
            load_query("authority_organization_exists"),
            uid=state.uid,
        )
        if await exists_result.single():
            raise ConflictError(f"AuthorityOrganization with uid {state.uid} already exists")

        # if 2 states were created in parallel with same identifiers (race condition), this will
        # ensure the state is reused rather than duplicated
        identifier_signature = cls.compute_identifier_signature(state.identifiers)

        state_from_graph = await tx.run(
            load_query("create_authority_organization_state"),
            identifier_signature=identifier_signature,
            uid=state.uid,
            normalized_name=state.normalized_name,
            display_names=state.display_names,
            org_type=state.type.value,
            source_organization_uids=state.source_organization_uids,
            excluded_identifiers=[t.value for t in (state.excluded_identifiers or [])],
        )

        await tx.run(load_query("delete_authority_organization_names"), uid=state.uid)
        await tx.run(
            load_query("create_authority_organization_names"),
            uid=state.uid,
            names=[n.model_dump() for n in state.names],
        )

        identifier_keys = [f"{i.type.value}:{i.value}" for i in state.identifiers]
        await tx.run(
            load_query("detach_authority_organization_identifier_rels"),
            uid=state.uid,
            identifier_keys=identifier_keys,
        )

        await tx.run(
            load_query("create_authority_organization_identifiers"),
            uid=state.uid,
            identifiers=[{"type": i.type.value, "value": i.value} for i in state.identifiers],
        )

        state_record = await state_from_graph.single()
        return state_record["o"]["uid"]

    @classmethod
    async def _update_authority_organization_state_tx(cls, tx: AsyncManagedTransaction,
                                                      state: AuthorityOrganizationState) -> None:
        exists_result = await tx.run(
            load_query("authority_organization_exists"),
            uid=state.uid,
        )
        if not await exists_result.single():
            raise NotFoundError(f"AuthorityOrganization with uid {state.uid} does not exist")

        identifier_signature = cls.compute_identifier_signature(state.identifiers)
        await tx.run(
            load_query("update_authority_organization_properties"),
            uid=state.uid,
            identifier_signature=identifier_signature,
            org_type=state.type.value,
            normalized_name=state.normalized_name,
            display_names=state.display_names,
            source_organization_uids=state.source_organization_uids,
            excluded_identifiers=[t.value for t in (state.excluded_identifiers or [])],
        )

        await tx.run(load_query("delete_authority_organization_names"), uid=state.uid)
        await tx.run(
            load_query("create_authority_organization_names"),
            uid=state.uid,
            names=[n.model_dump() for n in state.names],
        )

        identifier_keys = [f"{i.type.value}:{i.value}" for i in state.identifiers]
        await tx.run(
            load_query("detach_authority_organization_identifier_rels"),
            uid=state.uid,
            identifier_keys=identifier_keys,
        )

        await tx.run(
            load_query("create_authority_organization_identifiers"),
            uid=state.uid,
            identifiers=[{"type": i.type.value, "value": i.value} for i in state.identifiers],
        )


    @handle_database_errors
    async def get_authority_organization_state_by_uid(
            self,
            state_uid: str) -> AuthorityOrganizationState:
        """
        Retrieve an AuthorityOrganizationState by its UID.
        :param state_uid:
        :return:
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    result = await tx.run(
                        load_query("get_authority_organization_state_by_uid"),
                        state_uid=state_uid,
                    )
                    record = await result.single()
                    if not record:
                        raise NotFoundError(
                            f"AuthorityOrganizationState with uid {state_uid} not found")
                    return self._hydrate_authority_organization_state(record)

    @handle_database_errors
    async def get_authority_organization_root_by_uid(
            self,
            root_uid: str) -> AuthorityOrganizationRoot:
        """
        Retrieve an AuthorityOrganizationRoot by its UID.
        :param root_uid:
        :return:
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    result = await tx.run(
                        load_query("get_authority_organization_root_by_uid"),
                        root_uid=root_uid,
                    )
                    record = await result.single()
                    if not record:
                        raise NotFoundError(
                            f"AuthorityOrganizationRoot with uid {root_uid} not found")
                    return self._hydrate_authority_organization_root(record)

    @handle_database_errors
    async def create_authority_organization_root(self, root: AuthorityOrganizationRoot) -> str:
        """
        Create an AuthorityOrganizationRoot in the database.
        :param root:
        :return:
        """
        root.random_uid()
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    result = await tx.run(load_query("create_authority_organization_root"),
                                          uid=root.uid,
                                          source_organization_uids=root.source_organization_uids
                                          )
                    rec = await result.single()
                    return rec["r"]["uid"]

    @handle_database_errors
    async def find_organization_roots_of_states(self, state_uids: list[str]) -> list[str]:
        """
        Find the UIDs of AuthorityOrganizationRoots for the given AuthorityOrganizationStates.
        :param state_uids: list of AuthorityOrganizationState UIDs
        :return: list of AuthorityOrganizationRoot UIDs
        """

        if not state_uids:
            return []
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    result = await tx.run(
                        load_query("find_organization_roots_of_states"),
                        state_uids=state_uids,
                    )
                    rows = await result.data()
                    return [r["root_uid"] for r in rows]

    @handle_database_errors
    async def get_organization_states_of_root(self, root_uid: str) -> list[str]:
        """
        Get the UIDs of AuthorityOrganizationStates attached to an AuthorityOrganizationRoot.
        :param root_uid:
        :return:
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    result = await tx.run(
                        load_query("get_organization_states_of_root"),
                        root_uid=root_uid,
                    )
                    rec = await result.single()
                    return rec["state_uids"] if rec and rec["state_uids"] else []

    @handle_database_errors
    async def update_authority_organization_root(
            self,
            root: AuthorityOrganizationRoot,
    ) -> AuthorityOrganizationRoot:
        """
        Update scalar properties of an AuthorityOrganizationRoot.
        Relationships must be handled elsewhere.
        """
        if not root.uid:
            raise ValueError("AuthorityOrganizationRoot.uid is required to update")

        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    result = await tx.run(
                        load_query("update_authority_organization_root"),
                        uid=root.uid,
                        source_organization_uids=root.source_organization_uids or [],
                    )
                    record = await result.single()
                    if not record:
                        raise NotFoundError(
                            f"AuthorityOrganizationRoot with uid {root.uid} not found"
                        )
                    return self._hydrate_authority_organization_root(record)

    @handle_database_errors
    async def attach_authority_organization_states_to_root(self, root_uid: str,
                                                           state_uids: list[str]) -> None:
        """
        Attach AuthorityOrganizationStates to an AuthorityOrganizationRoot.
        :param root_uid:
        :param state_uids:
        :return:
        """
        if not state_uids:
            return
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                await session.write_transaction(
                    self._attach_authority_organization_states_to_root_tx,
                    root_uid,
                    state_uids,
                )

    @staticmethod
    async def _attach_authority_organization_states_to_root_tx(
            tx: AsyncManagedTransaction,
            root_uid: str,
            state_uids: list[str],
    ) -> None:
        await tx.run(
            load_query("attach_authority_organization_states_to_root"),
            root_uid=root_uid,
            state_uids=state_uids,
        )


    @handle_database_errors
    async def attach_place_and_address_nodes_to_state(self, state_uid: str,
                                            place_list: list(Place),
                                            address_list: list(StructuredPhysicalAddress)) -> None:
        """
        Create location information and link them to an AuthorityOrganizationState.
        :param state_uid:
        :param places:
        :param addresses:
        :return:
        """
        addresses = []
        if address_list:
            for address in address_list:
                address_dict = {
                    "uid": address.uid,
                    "street": [{"value": c.value, "language": c.language} for c in address.street if
                             c.value] or None,
                    "city": [{"value": c.value, "language": c.language} for c in address.city if
                             c.value] or None,
                    "zip_code": [{"value": c.value, "language": c.language} for c in
                                 address.zip_code if c.value] or None,
                    "state_or_province": [{"value": s.value, "language": s.language} for s in
                                          address.state_or_province if s.value] or None,
                    "country": [{"value": c.value, "language": c.language} for c in
                                address.country if c.value] or None,
                    "continent": [{"value": c.value, "language": c.language} for c in
                                address.country if c.value] or None
                }
                addresses.append(address_dict)

        places = [
            {"latitude": place.latitude, "longitude": place.longitude}
            for place in place_list
            if place.latitude is not None and place.longitude is not None
        ] if place_list else []

        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                await session.write_transaction(
                    self._attach_place_and_address_nodes_to_state,
                    state_uid,
                    places,
                    addresses
                )

    @staticmethod
    async def _attach_place_and_address_nodes_to_state(
            tx: AsyncManagedTransaction,
            state_uid: str,
            places: list,
            addresses: list
    ) -> None:

        await tx.run(
            load_query("update_authority_organization_state_addresses"),
            state_uid=state_uid,
            addresses=addresses
        )

        await tx.run(
            load_query("update_authority_organization_state_places"),
            state_uid=state_uid,
            places=places
        )


    @staticmethod
    def _norm_type(t: str) -> str:
        return re.sub(r"[^a-z]", "", t.lower())

    @classmethod
    def compute_identifier_signature(cls, identifiers) -> str:
        """
        Compute a signature hash for a set of organization identifiers.
        The signature is based on the normalized type and value of each identifier,
        sorted and concatenated, then hashed using SHA-256.
        :param identifiers:
        :return:
        """
        items = sorted(
            (cls._norm_type(i.type.value), i.value)
            for i in identifiers
        )
        raw = "|".join(f"{t}:{v}" for t, v in items)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @classmethod
    def _hydrate_authority_organization_root(cls, record) -> AuthorityOrganizationRoot:
        r = record["r"]

        hydrated_states: list[AuthorityOrganizationState] = []
        for state_row in (record.get("states") or []):
            if not state_row:
                continue
            hydrated_states.append(cls._hydrate_authority_organization_state(state_row))

        return AuthorityOrganizationRoot(
            uid=r["uid"],
            display_names=r.get("display_names") or [],
            states=hydrated_states,
            source_organization_uids=r.get("source_organization_uids") or [],
        )

    @staticmethod
    def _hydrate_authority_organization_state(record) -> AuthorityOrganizationState:
        o = record["o"]
        names = [Literal(**n) for n in record["names"]]
        identifiers = [OrganizationIdentifier(**i) for i in record["identifiers"]]

        raw_excluded_identifiers = o.get("excluded_identifiers") or []
        excluded = []
        for type_str in raw_excluded_identifiers:
            enum_type = OrganizationIdentifierType.from_str(type_str)
            if enum_type:
                excluded.append(enum_type)

        org_type = o.get("type") or SourceOrganization.SourceOrganisationType.ORGANIZATION.value
        return AuthorityOrganizationState(
            uid=o["uid"],
            type=SourceOrganization.SourceOrganisationType(org_type),
            source_organization_uids=o.get("source_organization_uids") or [],
            names=names,
            display_names=o.get("display_names") or [],
            normalized_name=o.get("normalized_name"),
            identifiers=identifiers,
            excluded_identifiers=excluded,
        )
