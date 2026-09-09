# Affiliation's type update failure to fix

Issue: https://github.com/CRISalid-esr/crisalid-ikg/issues/415

## Context

In SoVisu+, a user changes the type of a contributor's affiliation. HAL knows exactly six
structure types (`type_s` facet of
https://api.archives-ouvertes.fr/ref/structure/?q=*:*&rows=0&facet=true&facet.field=type_s):
`institution`, `laboratory`, `researchteam`, `department`, `regrouplaboratory`,
`regroupinstitution`. The edit leaves the app as a contribution-update
user action carrying the full contributor list, each affiliation carrying its HAL
`type` string. The type change is silently lost: the graph keeps the previous value and
the refreshed document shows the old type again.

### How the type flows today

1. **Inbound**: `AMQPUserActionsMessageProcessor` stores the `Change` (path
   `contributions`) and applies it through `DocumentContributionsChangeProcessor` →
   `ContributionUpdateService.reconcile`.
2. **Affiliation resolution**: `ContributionUpdateService._build_source_organization`
   builds an in-memory `SourceOrganization` per affiliation, mapping the HAL type through
   `_ORG_TYPE_MAP` (unknown value → generic `ORGANIZATION`), then
   `_resolve_affiliations` calls
   `AuthorityOrganizationService.get_or_create_authority_organization([organisation])`
   for each of them.
3. **In-memory state**: `split_cluster_into_root_and_states` creates a fresh
   `AuthorityOrganizationState` (default type `ORGANIZATION`) and
   `_enrich_states_from_sources` copies the single source's type onto it. This step is
   not a problem for the user path: the state is new, so the submitted type is always
   applied here.
4. **Persistence** (the actual break): `_get_or_create_state_in_graph_by_identifier`
   finds the persisted state matched by the HAL identifier and only lets the submitted
   type through when the persisted state still carries the generic type:

   ```python
   if (selected.type == ORGANIZATION and desired.type != ORGANIZATION):
       selected.type = desired.type
   ```

   Any state that already has a real type keeps it, `update_authority_organization_properties`
   rewrites the old value, and the outbound document event carries the old type.

The same method is used by the harvest path
(`SourceContributorMappingService._map_source_organizations_to_authority_organization_states`),
where the guard is legitimate: a harvester must not downgrade a typed state to the
generic placeholder.

### Why simply removing the guard is not enough

The type lives on the **shared** `AuthorityOrganizationState`, not on the affiliation
statement, while user changes are stored and replayed **per document**
(`ChangeService.apply_changes_to_node` at the end of every document recomputation).
With a "last writer wins" rule on both paths:

1. The user sets the type from document A; the shared state carries the new type.
2. Document B, affiliated to the same HAL structure, is re-harvested; its recomputation
   goes through the harvest path and writes the HAL type back onto the shared state.
3. B's replay does not help (B has no contributions change) and A's change is not
   replayed because A was not recomputed. A displays the old type again.

The replay only protects the same document; the shared state needs its own protection.

### Secondary defects

- `department` is one of the six HAL structure types and is offered by the UI, but it is
  absent from `_ORG_TYPE_MAP` and from `SourceOrganisationType`: selecting it falls back
  to the generic `ORGANIZATION`, which the UI renders as "None". Conversely
  `regroupresearchteam` (`RESEARCH_TEAM_GROUP`) is mapped but does not exist in HAL.
- On the user path, `selected.set_names(desired.names)` replaces the state's
  accumulated names with the single message name; a message with an empty or missing
  `name`/`label` wipes the display names of a shared state.

### Known limitation (kept, documented)

One type per shared state: two users editing the same structure from two different
documents overwrite each other. Moving the type onto the `HAS_AFFILIATION_STATEMENT`
relationship would be a graph-model and GraphQL change and is out of scope.

## Goal

A type submitted by a user action is applied to the affiliation's authority state and
is never overwritten by a later harvest, on any document. Harvest behaviour on states
never touched by a user is unchanged.

Invariants after the change:

1. A contribution-update message carrying a recognized HAL type sets that type on the
   resolved `AuthorityOrganizationState`, whatever the previous value.
2. A state whose type was set by a user keeps it through any later harvest of any
   document (the harvest path never overwrites a user-set type).
3. On states never touched by a user, the harvest path behaves exactly as today (only a
   generic type is replaced).
4. `department` round-trips: message `"department"` → state type `department` →
   outbound event `department`.
5. A user-action affiliation never removes names from a shared state.

## Design

### A. Record the type provenance on the state

Add to `AuthorityOrganizationState`:

```python
class TypeOrigin(Enum):
    HARVEST = "harvest"   # default: set from harvested source organizations
    USER = "user"         # set by a user action, protected from harvest overwrite

type_origin: TypeOrigin = TypeOrigin.HARVEST
```

Persist it as `o.type_origin` in `create_authority_organization_state.cypher`
(`ON CREATE` and `ON MATCH`) and `update_authority_organization_properties.cypher`;
hydrate it in `AuthorityOrganizationDAO` with a fallback to `harvest` when the property
is missing (existing nodes). No migration: an absent property means harvest origin.

### B. Authoritative type flag on the user path

`AuthorityOrganizationService.get_or_create_authority_organization` gains a keyword
parameter `type_authoritative: bool = False`, forwarded to
`_get_or_create_state_in_graph_by_identifier`. `ContributionUpdateService`
`_resolve_affiliations` passes `type_authoritative=True` only when the affiliation's
message type mapped to a recognized non-generic type; a missing or unmapped type is
treated like a harvest default (no override) and an unmapped value adds an
`AFFILIATION_TYPE_UNKNOWN` warning to the `ChangeApplicationReport` (type value and
source organization uid in the details). The harvest caller is unchanged.

Since `_resolve_affiliations` resolves one source organization at a time, the flag is
computed per affiliation.

### C. Merge rule in `_get_or_create_state_in_graph_by_identifier`

Replace the current guard by:

```python
if type_authoritative:
    selected.type = desired.type
    selected.type_origin = TypeOrigin.USER
elif (selected.type_origin != TypeOrigin.USER
      and selected.type == ORGANIZATION
      and desired.type != ORGANIZATION):
    selected.type = desired.type          # origin stays HARVEST
```

On the create branch (no compatible candidate), set `desired.type_origin = USER` before
`create_authority_organization_state` when the flag is set. `_enrich_states_from_sources`
is unchanged.

The name-based branch of `get_or_create_authority_organization` (states without
identifiers) is not concerned: user-action affiliations always carry the HAL identifier.

Following a genuine retyping of a structure in HAL on harvest-origin states is a
possible follow-up (the origin flag now makes it safe) and is not part of this issue.

### D. `department` support

Add `DEPARTMENT = "department"` to `SourceOrganization.SourceOrganisationType` and
`"department": DEPARTMENT` to `ContributionUpdateService._ORG_TYPE_MAP`, so that the map
covers the six HAL types. Check that nothing enumerates the enum exhaustively (search for
`SourceOrganisationType.` usages and any mapping keyed on its members); no other layer of
this repository needs the value.

Keep `RESEARCH_TEAM_GROUP` / `"regroupresearchteam"`: it is unreachable from HAL but
harmless, and removing an enum member could break hydration of existing nodes.

### E. Names on the user path

In `_get_or_create_state_in_graph_by_identifier`, when `type_authoritative` is set (user
path), names are merged, not replaced: `selected.set_names(selected.names + desired.names)`
(`set_names` already deduplicates by language and value). The harvest path keeps the
replacement, since the cluster carries every source's name.

## Tests

All tests run against the real Neo4j test instance (`APP_ENV=TEST pytest`). Reuse the
fixtures and helpers of `tests/test_services/test_contribution_update_service.py`
(document with a HAL-affiliated contribution, contribution-update change builder).

1. **Model and persistence**: `AuthorityOrganizationState` defaults to
   `type_origin == HARVEST`; a state created with `USER` origin round-trips through the
   DAO; a node without the `type_origin` property hydrates to `HARVEST`.
2. **User override on a typed state**: a state with type `laboratory` (harvest origin)
   resolved by a contribution-update message with `"type": "institution"` ends with
   type `institution` and origin `user`; the outbound document event carries
   `institution`.
3. **Harvest never overwrites a user type**: after test 2, a second document whose HAL
   source record affiliates the same structure with type `laboratory` is created and
   recomputed; the shared state still has type `institution` and origin `user`, and the
   first document's contribution still points to that state.
4. **Same-document replay**: after test 2, the first document is recomputed from its
   source records; the replayed contributions change keeps type `institution`.
5. **Harvest fills only a generic type, unchanged behaviour**: a state with type
   `organization` (harvest origin) resolved by a harvested `laboratory` source becomes
   `laboratory` with origin `harvest`; a state with type `laboratory` resolved by a
   harvested `institution` source keeps `laboratory`.
6. **Unknown or missing type on the user path**: a message with `"type": null` or
   `"type": "foo"` leaves a typed state untouched (type and origin) and, for `"foo"`,
   adds an `AFFILIATION_TYPE_UNKNOWN` warning to the report.
7. **`department`**: a message with `"type": "department"` yields state type
   `department`, persisted and present in the outbound event.
8. **Names are preserved**: a state with display names `["Lab A", "Laboratoire A"]`
   resolved by a message with `"name": "Lab A"` keeps both names; a message with no
   `name` and no `label` leaves the names untouched.

Run `pylint --rcfile=.pylintrc app/` before committing; the score must not regress.
