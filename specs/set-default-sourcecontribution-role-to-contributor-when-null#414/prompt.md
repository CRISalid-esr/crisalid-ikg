# Set default SourceContribution role to "Contributor" when null

Issue: https://github.com/CRISalid-esr/crisalid-ikg/issues/414

## Context

Downstream consumers (SoVisu+) are notified about source contributions carrying a null
role, and the graph contains `Contribution` nodes with an empty `roles` list, which
propagate as `"roles": []` in outbound document events.

### How roles flow today

1. **Inbound**: `AMQPReferenceMessageProcessor` builds `SourceRecord(**reference_data)`.
   `SourceContribution.role` is `Optional[LocContributionRole]`; the `validate_role`
   field validator returns `None` in two distinct cases:
   - the payload carries no role (or a non-string value);
   - the role URL does not map to a LoC relator (logs `Invalid contribution role`).
2. **Source layer write**: `SourceRecordDAO._create_contribution_transaction` passes
   `role=source_contribution.role.name if source_contribution.role else None` to
   `create_source_contribution.cypher` (`SET sc.role = $role`). A null parameter leaves
   the `SourceContribution` node without a `role` property (stores the enum **name**,
   e.g. `"AUTHOR"`).
3. **Hydration**: `SourceRecordDAO._hydrate_contributions` maps a missing or
   unrecognized `role` property back to `role=None`.
4. **Document merge**: `SourceContributorMappingService._get_roles_by_harvester_order`
   skips `None` roles, so a person whose source contributions all lack a role gets
   `Contribution.roles = []` (stores the enum **values**, i.e. LoC URIs).
5. **Second write path**: `ContributionUpdateService.reconcile` (sovisuplus
   contribution-update messages) does `roles = contribution.get("roles") or []` and
   writes them verbatim — an empty or missing list also yields `Contribution.roles = []`.
6. **Outbound**: `AMQPDocumentEventMessageFactory` serializes
   `contribution.model_dump()`, so the empty list reaches subscribers.

### Neo4j database findings (2026-07-24, publications only partially loaded)

- 210,338 `SourceContribution` nodes; **624 have no `role`** — all of them harvested by
  **idref** (Sudoc records).
- 130,000 `Contribution` nodes; **554 have `roles = []`** (none have `roles IS NULL`).
- For every one of those 554 contributions, the roles collected over the person's source
  contributions on the document's source records reduce to `[]` (all null) — the
  propagation chain above is confirmed as the only cause. All affected documents include
  an idref source record.

## Goal

A contribution role is never null/empty anywhere in the pipeline: when a source does not
provide a usable role, the contribution defaults to the generic LoC **Contributor** role
(`http://id.loc.gov/vocabulary/relators/ctb` / `LocContributionRole.CONTRIBUTOR`).

Invariants after the change:

1. `SourceContribution.role` (model) is never `None`.
2. `SourceContribution.role` (graph property) is always set (enum name, default
   `"CONTRIBUTOR"`).
3. `Contribution.roles` (graph property and outbound payload) is never empty.

## Design

### A. Default at the `SourceContribution` model level

Make the default a model invariant so every producer (inbound message parsing **and**
graph hydration) benefits without duplicating the rule:

- `role: LocContributionRole = LocContributionRole.CONTRIBUTOR` (no longer `Optional`);
- `validate_role` keeps its current logic but returns
  `LocContributionRole.CONTRIBUTOR` instead of `None` in both null cases (absent role and
  unrecognized URI — keep the error log for the latter);
- `SourceRecordDAO._hydrate_contributions` no longer needs the `role = None` fallbacks:
  a missing or unrecognized property hydrates to `CONTRIBUTOR`.

`SourceRecordDAO._create_contribution_transaction` can drop the `if ... else None` guard
(`role=source_contribution.role.name`); `create_source_contribution.cypher` is unchanged.

Rationale for defaulting the unrecognized-URI case too: the alternative (keeping `None`)
would preserve the very state this issue removes; a generic Contributor role plus the
existing error log loses no information that the graph was keeping anyway.

### B. Generic-role dedup in the document merge

With the default in place, a person harvested with `aut` from one source and no role from
another would collect `roles = [AUTHOR, CONTRIBUTOR]`. Since Contributor is the generic
fallback (and is implied by any specific relator), `_get_roles_by_harvester_order`
drops `CONTRIBUTOR` whenever at least one other role was collected: it is kept only when
it is the sole role. This also applies to genuine harvested `ctb` roles, which is
semantically harmless (`aut` subsumes `ctb`).

### C. Default in `ContributionUpdateService.reconcile`

Replace `roles = contribution.get("roles") or []` with a default to
`[LocContributionRole.CONTRIBUTOR.value]` when the message provides no non-empty role
list, so the sovisuplus path upholds invariant 3 as well.

### Out of scope: data migration

No migration of existing null-role `SourceContribution` / empty-roles `Contribution`
nodes: the Neo4j database will be wiped and reloaded, so only newly written data
matters.

## Tests

All tests run against the real Neo4j test instance (`APP_ENV=TEST pytest`).

1. **Model default**: `SourceContribution` built with `role` absent, `role=None`, and an
   unrecognized role URL all end with `role == LocContributionRole.CONTRIBUTOR`; a valid
   role URL still maps to its relator.
2. **Source-layer roundtrip**: persisting a source record whose contribution has no role
   stores `sc.role = 'CONTRIBUTOR'`; hydrating a `SourceContribution` node without a
   `role` property (defensive case) yields `CONTRIBUTOR`.
3. **Merge, sole default**: a document whose only source record (idref-like fixture with
   roleless contributions) is merged → each `Contribution.roles ==
   ['http://id.loc.gov/vocabulary/relators/ctb']`.
4. **Merge, generic-role dedup**: same person with `aut` from one source record and no
   role from another → `Contribution.roles == ['.../aut']` (no `ctb`); a person with a
   genuine `ctb` plus `aut` also ends with `['.../aut']`.
5. **Contribution-update path**: a sovisuplus contribution-update message with missing or
   empty `roles` produces a contribution with `roles == ['.../ctb']`; a message with
   explicit roles is untouched.
6. **Outbound payload**: the document event built from case 3 carries the `ctb` role
   (no empty `roles` list).
