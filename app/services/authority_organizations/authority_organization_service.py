from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Set, Optional

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao_factory import DAOFactory
from app.graph.neo4j.authority_organization_dao import AuthorityOrganizationDAO
from app.models.agent_identifiers import OrganizationIdentifier
from app.models.authority_organization_root import AuthorityOrganizationRoot
from app.models.authority_organization_state import AuthorityOrganizationState
from app.models.identifier_types import OrganizationIdentifierType
from app.models.literal import Literal
from app.models.source_organization_identifiers import SourceOrganizationIdentifier
from app.models.source_organizations import SourceOrganization
from app.signals import authority_organisation_state_updated


class AuthorityOrganizationService:
    """
    Resolve SourceOrganizations (cluster) into AuthorityOrganizationState(s),
    then get-or-create states in Neo4j.
    """

    # pylint: disable=too-many-locals, too-many-branches, too-many-statements, too-many-return-statements
    async def get_or_create_authority_organization(
            self,
            source_org_cluster: List[SourceOrganization],
    ) -> AuthorityOrganizationRoot:
        """
        Build AuthorityOrganizationRoot + AuthorityOrganizationState(s) from a source-org cluster.
        For each state, get-or-create it in Neo4j (states are labeled :AuthorityOrganization too).
        """
        in_memory_root = self.split_cluster_into_root_and_states(source_org_cluster)

        dao = self._get_authority_org_dao()

        persisted_states: List[AuthorityOrganizationState] = []
        for state in in_memory_root.states:
            if state.identifiers:
                persisted_states.append(
                    await self._get_or_create_state_in_graph_by_identifier(dao, state))
                await self._signal_state_updated(persisted_states[-1].uid)
            elif state.normalized_name:
                # handle case of state without identifiers
                matching_states = await dao.get_states_by_normalized_name(state.normalized_name)
                if len(matching_states) == 0:
                    new_state = await dao.create_authority_organization_state(state)
                    await self._signal_state_updated(new_state.uid)
                    persisted_states.append(new_state)
                elif len(matching_states) == 1:  # an homonym was either found, either created
                    persisted_states.append(matching_states[0])
                else:
                    # if we found a state without identifiers, let's take it
                    state_without_identifiers = next(
                        (s for s in matching_states if not s.identifiers),
                        None,
                    )
                    if state_without_identifiers:
                        persisted_states.append(state_without_identifiers)
                    else:  # if all states have a common root, take that root's state
                        roots = await dao.find_organization_roots_of_states(
                            [c.uid for c in matching_states])
                        if len(roots) == 1:
                            return await dao.get_authority_organization_root_by_uid(roots[0])
                        # as we cannot choose among homonyms, create a new state without identifiers
                        new_state = await dao.create_authority_organization_state(state)
                        await self._signal_state_updated(new_state.uid)
                        persisted_states.append(new_state)

        in_memory_root.states = persisted_states

        needs_root = len(in_memory_root.states) > 1 or len(
            in_memory_root.source_organization_uids) > 0
        cluster_state_uids = [s.uid for s in in_memory_root.states]

        # If no root is needed for this cluster, just return a wrapper root object
        if not needs_root:
            in_memory_root.uid = None
            return in_memory_root

        roots = await dao.find_organization_roots_of_states(cluster_state_uids)
        if len(roots) == 0:
            # if no root exists yet, create one and link it to states
            new_root_uid = await dao.create_authority_organization_root(in_memory_root)
            await dao.attach_authority_organization_states_to_root(
                root_uid=new_root_uid,
                state_uids=[s.uid for s in in_memory_root.states if s.uid],
            )
            return await dao.get_authority_organization_root_by_uid(new_root_uid)
        if len(roots) == 1:
            root_uid = roots[0]
            attached = await dao.get_organization_states_of_root(root_uid)
            # if the root has states that are not in the cluster, create a new root
            if any(uid not in cluster_state_uids for uid in attached):
                new_root_uid = await dao.create_authority_organization_root(in_memory_root)
                await dao.attach_authority_organization_states_to_root(
                    root_uid=new_root_uid,
                    state_uids=[s.uid for s in in_memory_root.states if s.uid],
                )
                return await dao.get_authority_organization_root_by_uid(new_root_uid)
            # case where all attached states are in the cluster:
            # reuse existing root
            await dao.attach_authority_organization_states_to_root(
                root_uid=root_uid,
                state_uids=[s.uid for s in in_memory_root.states if s.uid],
            )
            # overwrite other root properties
            in_memory_root.uid = root_uid
            return await dao.update_authority_organization_root(in_memory_root)
        # case of multiple roots found for the same cluster
        states_by_root: Dict[str, List[str]] = {}
        for root_uid in roots:
            attached = await dao.get_organization_states_of_root(root_uid)
            states_by_root[root_uid] = attached
        # we will choose the root having the largest number of attached states
        # among those whose states are all in the cluster
        # order roots by number of attached states (descending)
        sorted_roots = sorted(
            states_by_root.items(),
            key=lambda item: len(item[1]),
            reverse=True,
        )
        for root_uid, attached in sorted_roots:
            if all(uid in cluster_state_uids for uid in attached):
                # found a root whose states are all in the cluster
                await dao.attach_authority_organization_states_to_root(
                    root_uid=root_uid,
                    state_uids=[s.uid for s in in_memory_root.states if s.uid],
                )
                in_memory_root.uid = root_uid
                await dao.update_authority_organization_root(in_memory_root)
                return await dao.get_authority_organization_root_by_uid(root_uid)
        # no suitable root found, create a new one
        new_root_uid = await dao.create_authority_organization_root(in_memory_root)
        await dao.attach_authority_organization_states_to_root(
            root_uid=new_root_uid,
            state_uids=[s.uid for s in in_memory_root.states if s.uid],
        )
        return await dao.get_authority_organization_root_by_uid(new_root_uid)

    @classmethod
    def split_cluster_into_root_and_states(
            cls,
            source_orgs: List[SourceOrganization],
    ) -> AuthorityOrganizationRoot:
        """
        Split a cluster of SourceOrganizations into an AuthorityOrganizationRoot
        and its AuthorityOrganizationStates, based on identifier compatibility.
        The method does not create or update anything in the graph database.
        It only builds the in-memory representation of the root and its states.
        :param source_orgs: List of SourceOrganizations in the cluster.
        :return: AuthorityOrganizationRoot with its states.
        """

        ambiguous_identifiers_by_uid: Dict[str, Set[str]] = {
            so.uid: so.get_ambiguous_identifiers()
            for so in source_orgs
        }

        prepared = cls._prepare_source_orgs(source_orgs)

        identifiers_by_uid: Dict[str, Dict[str, str]] = {
            so.uid: {ident.type: ident.value for ident in so.identifiers}
            for so in prepared
        }

        incompatibilities = cls._build_incompatibility_adjacency(identifiers_by_uid,
                                                                 ambiguous_identifiers_by_uid)

        conflicting_uids = [uid for uid, neigh in incompatibilities.items() if neigh]
        conflicting_uids.sort(key=lambda uid: len(incompatibilities[uid]), reverse=True)

        states: List[AuthorityOrganizationState] = []
        assigned: Set[str] = set()

        # 1) seed states with conflicting source orgs
        for uid in conflicting_uids:
            if uid in assigned:
                continue
            identifiers = identifiers_by_uid[uid]
            # check that none of the conflicting source org uid are already assigned
            compatible = [state for state in states if cls._is_compatible(
                state,
                identifiers,
                incompatibilities.get(uid, set()),
                ambiguous_identifiers_by_uid[uid],
            )]

            if len(compatible) == 1:
                cls._attach(uid, identifiers, compatible[0], ambiguous_identifiers_by_uid[uid])
                assigned.add(uid)
            else:
                new_state = AuthorityOrganizationState()
                cls._attach(uid, identifiers, new_state, ambiguous_identifiers_by_uid[uid])
                states.append(new_state)
                assigned.add(uid)

        # 2) if no conflicts, create a single state seeded from first org
        # source organisations without identifiers (forcely alone) are handled here
        if not states and prepared:
            first = prepared[0]
            new_state = AuthorityOrganizationState()
            cls._attach(first.uid, identifiers_by_uid[first.uid], new_state,
                        ambiguous_identifiers_by_uid[first.uid])
            states.append(new_state)
            assigned.add(first.uid)

        # 3) assign remaining source orgs to exactly one compatible state, else to root_only
        root_only: List[str] = []
        for uid, identifiers in identifiers_by_uid.items():
            if uid in assigned:
                continue
            compatible = [state for state in states if cls._is_compatible(
                state,
                identifiers,
                incompatibilities.get(uid, set()),
                ambiguous_identifiers_by_uid[uid],
            )]
            if len(compatible) == 1:
                cls._attach(uid, identifiers, compatible[0], ambiguous_identifiers_by_uid[uid])
                assigned.add(uid)
            else:
                root_only.append(uid)

        cls._enrich_states_from_sources(states, source_orgs)

        return AuthorityOrganizationRoot(
            states=states,
            source_organization_uids=root_only,
        )

    @classmethod
    def _prepare_source_orgs(cls, source_orgs: List[SourceOrganization]) -> List[
        SourceOrganization]:
        """
        Return SourceOrganizations where ambiguous identifier types (multiple values
        for the same type on the same org) are removed.
        """
        prepared: List[SourceOrganization] = []
        for so in source_orgs:
            values_by_type: dict[str, set[str]] = defaultdict(set)
            for ident in so.identifiers or []:
                values_by_type[ident.type].add(ident.value)

            usable_identifiers: list[SourceOrganizationIdentifier] = [
                SourceOrganizationIdentifier(type=t, value=next(iter(values)))
                for t, values in values_by_type.items()
                if len(values) == 1
            ]

            prepared.append(
                SourceOrganization(
                    uid=so.uid,
                    source=so.source,
                    source_identifier=so.source_identifier,
                    name=so.name,
                    type=so.type,
                    identifiers=usable_identifiers,
                )
            )
        return prepared

    @classmethod
    def _build_incompatibility_adjacency(
            cls,
            identifiers_by_uid: Dict[str, Dict[str, str]],
            ambiguous_identifiers_by_uid: Dict[str, Set[str]],
    ) -> Dict[str, Set[str]]:
        """
        Build incompatibility adjacency:

        - Base rule: incompatible if same type but different value.
        - Ambiguity rule: if uid has ambiguous type t (multiple values),
          then uid is incompatible with ANY other uid that has type t at all
          (regardless of value).

        Returns: uid -> set(incompatible_uids)
        """

        # type -> value -> set(uids)
        uids_by_type_value: Dict[str, Dict[str, Set[str]]] = {}
        # type -> set(uids having this type)
        uids_by_type: Dict[str, Set[str]] = {}

        for uid, sig in identifiers_by_uid.items():
            for t, v in sig.items():
                uids_by_type_value.setdefault(t, {}).setdefault(v, set()).add(uid)
                uids_by_type.setdefault(t, set()).add(uid)

        adjacency: Dict[str, Set[str]] = {uid: set() for uid in identifiers_by_uid.keys()}

        # pylint: disable=too-many-nested-blocks
        for t, groups in uids_by_type_value.items():
            vals = list(groups.keys())
            if len(vals) <= 1:
                continue
            # pylint: disable=consider-using-enumerate
            for i in range(len(vals)):
                for j in range(i + 1, len(vals)):
                    left = groups[vals[i]]
                    right = groups[vals[j]]
                    for u in left:
                        for v in right:
                            if u == v:
                                continue
                            adjacency[u].add(v)
                            adjacency[v].add(u)

        # if uid is ambiguous for type t, it's incompatible with everyone who has type t
        for uid, amb_types in ambiguous_identifiers_by_uid.items():
            for t in amb_types:
                others = uids_by_type.get(t, set())
                for v in others:
                    if v == uid:
                        continue
                    adjacency[uid].add(v)
                    adjacency[v].add(uid)

        return adjacency

    @classmethod
    def _is_compatible(
            cls,
            state: AuthorityOrganizationState,
            identifiers: dict[str, str],
            incompatible_neighbors: set[str],
            incoming_excluded_types: Optional[set[str]] = None,
    ) -> bool:
        """
        Compatibility =

        A) adjacency rule (computed from incompatibility graph): uid must not be incompatible
           with any already-attached uid in the state

        B) exclusion rule (bidirectional):
           - if incoming excludes type t, state must not contain t (neither usable nor excluded)
           - if state excludes type t, incoming must not contain t (neither usable nor excluded)

        C) base rule: no contradictory type/value among usable identifiers
        """

        # --- A) adjacency rule ---
        if incompatible_neighbors and any(
                neigh in state.source_organization_uids for neigh in incompatible_neighbors
        ):
            return False

        # --- B) exclusion rule (bidirectional) ---

        # Incoming excluded as enum set
        incoming_excluded: Set[OrganizationIdentifierType] = set()
        for t in (incoming_excluded_types or set()):
            tt = OrganizationIdentifierType.from_str(t)
            if tt is not None:
                incoming_excluded.add(tt)

        # Incoming usable identifier types as enum set
        incoming_types: Set[OrganizationIdentifierType] = set()
        for t in identifiers.keys():
            tt = OrganizationIdentifierType.from_str(t)
            if tt is not None:
                incoming_types.add(tt)

        # State usable identifier types + state excluded types
        state_types: Set[OrganizationIdentifierType] = {i.type for i in (state.identifiers or [])}
        state_excluded: Set[OrganizationIdentifierType] = set(state.excluded_identifiers or [])

        # If either side excludes type t,
        # it must not cohabit with any presence of t on the other side
        if incoming_excluded & state_types:
            return False
        if state_excluded & incoming_types:
            return False

        # --- C) classic type/value conflicts among usable identifiers ---
        state_identifiers = {i.type.value: i.value for i in (state.identifiers or [])}
        for t, v in identifiers.items():
            org_id_type = OrganizationIdentifierType.from_str(t)
            if org_id_type is None:
                continue
            key = org_id_type.value
            if key in state_identifiers and state_identifiers[key] != v:
                return False

        return True

    @classmethod
    def _attach(
            cls,
            uid: str,
            identifiers: dict[str, str],
            state: AuthorityOrganizationState,
            excluded_types: set[str] | None = None,
    ) -> None:
        if uid not in state.source_organization_uids:
            state.source_organization_uids.append(uid)

        # --- attach excluded identifiers ---
        for t in (excluded_types or set()):
            org_id_type = OrganizationIdentifierType.from_str(t)
            if org_id_type is None:
                continue
            if org_id_type not in state.excluded_identifiers:
                state.excluded_identifiers.append(org_id_type)

        # --- attach usable identifiers (1 value per type in identifiers dict) ---
        existing = {(i.type.value, i.value) for i in state.identifiers}
        for t, v in identifiers.items():
            org_id_type = OrganizationIdentifierType.from_str(t)
            if org_id_type is None:
                continue

            key = (org_id_type.value, v)
            if key in existing:
                continue

            state.identifiers.append(OrganizationIdentifier(type=org_id_type, value=v))
            existing.add(key)

    @classmethod
    def _enrich_states_from_sources(
            cls,
            states: List[AuthorityOrganizationState],
            source_orgs: List[SourceOrganization],
    ) -> None:
        so_by_uid = {so.uid: so for so in source_orgs}

        for state in states:
            sources = [so_by_uid[uid] for uid in state.source_organization_uids if uid in so_by_uid]
            if not sources:
                continue

            # choose first non-generic type
            if state.type == SourceOrganization.SourceOrganisationType.ORGANIZATION:
                for source in sources:
                    if source.type != SourceOrganization.SourceOrganisationType.ORGANIZATION:
                        state.type = source.type
                        break

            names_set: Set[str] = set()
            for source in sources:
                if source.name and source.name.strip():
                    names_set.add(source.name.strip())
            state.set_names([Literal(value=n) for n in names_set])

    async def _get_or_create_state_in_graph_by_identifier(
            self,
            dao: AuthorityOrganizationDAO,
            desired: AuthorityOrganizationState,
    ) -> AuthorityOrganizationState:
        """
        Find compatible state in graph, or create new one.
        """
        candidates = await dao.get_states_with_compatible_identifiers(desired.identifiers)
        candidates = [c for c in candidates if self._passes_excluded_identifiers(desired, c)]

        if len(candidates) == 0:
            return await dao.create_authority_organization_state(desired)

        # case where compatible states are found (potentially more than one) :
        # select the candidate with the most identifiers
        # in case of race condition, where compatible states were created concurrently,
        # this will ensure the survival of the most complete state
        # and the disappearance of the less complete ones in future merges
        candidates.sort(key=lambda s: len(s.identifiers), reverse=True)
        selected = candidates[0]

        existing_keys = {(i.type.value, i.value) for i in selected.identifiers}
        for ident in desired.identifiers:
            k = (ident.type.value, ident.value)
            if k not in existing_keys:
                selected.identifiers.append(ident)
                existing_keys.add(k)

        if (
                selected.type == SourceOrganization.SourceOrganisationType.ORGANIZATION
                and desired.type != SourceOrganization.SourceOrganisationType.ORGANIZATION
        ):
            selected.type = desired.type

        selected.set_names(desired.names)

        # Merge exclusions (only add, never remove)
        selected_excluded_identifiers = set(selected.excluded_identifiers or [])
        desired_excluded_identifier = set(desired.excluded_identifiers or [])
        merged_excluded_identifiers = selected_excluded_identifiers | desired_excluded_identifier
        if merged_excluded_identifiers != selected_excluded_identifiers:
            selected.excluded_identifiers = list(merged_excluded_identifiers)

        return await dao.update_authority_organization_state(selected)

    async def _signal_state_updated(self, state_uid):
        """
        Signal that a document has been updated for all listeners to be notified
        :param document_uid:
        :return:
        """
        await authority_organisation_state_updated.send_async(self, state_uid=state_uid)

    @staticmethod
    def _passes_excluded_identifiers(
            desired: AuthorityOrganizationState,
            candidate: AuthorityOrganizationState,
    ) -> bool:
        desired_types = {i.type for i in desired.identifiers or []}
        candidate_types = {i.type for i in candidate.identifiers or []}

        desired_excl = set(desired.excluded_identifiers or [])
        candidate_excl = set(candidate.excluded_identifiers or [])

        # If candidate excludes T, desired must not contain T
        if candidate_excl & desired_types:
            return False

        # If desired excludes T, candidate must not contain T
        if desired_excl & candidate_types:
            return False

        return True

    @staticmethod
    def _get_dao_factory() -> DAOFactory:
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)

    def _get_authority_org_dao(self) -> AuthorityOrganizationDAO:
        factory = self._get_dao_factory()
        # Your DAO factory likely ignores the model type, but keep consistent with your pattern:
        return factory.get_dao(AuthorityOrganizationState)
