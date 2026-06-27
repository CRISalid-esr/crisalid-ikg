# Handle contribution update message coming from sovisuplus

Issue: https://github.com/CRISalid-esr/crisalid-ikg/issues/391

## Context

When a user edits the **Authors** tab of a document in sovisuplus and clicks *save*, sovisuplus
emits **one authoritative message describing the new, complete state of the document's
contributions**.

This replaces the originally-proposed series of atomic per-change messages (one `ADD` / `UPDATE` /
`REMOVE` per contributor, sequenced with `id` / `nextId`). The sovisuplus side has already been
changed accordingly — see
`/home/joachim/WebstormProjects/sovisuplus/specs/send-global-contributor-update-message/prompt.md`.

CRISalid IKG must receive this single message and **replace** the document's contribution set with
the state it carries:

- contributors present in the message are created / updated;
- contributors absent from it are removed;
- an empty contribution list removes all contributors.

The message is treated as **declarative full state**, not a delta. This matters because the change is
applied in two contexts:

1. **Interactive** — the user saves in the Authors tab (this message), processed from the
   interactive user-actions queue.
2. **Batch replay** — when the document is recomputed/merged from source records (harvesting), the
   stored `Change` is replayed via `ChangeService.apply_changes_to_node()`
   (`app/services/documents/document_service.py`). A declarative full-state change replays
   idempotently against a regenerated contribution graph; uid-keyed deltas would not.

The only difference between the two contexts is the **queue / `MessageMode`** of the outbound
"document updated" message (interactive vs batch).

## Message contract

- `actionType`: `"UPDATE"` (reused; no new action type)
- `targetType`: `"DOCUMENT"`
- `path`: `"contributions"`
- Routing key: `task.documents.document.update` (→ inbound user-actions queue)
- `parameters.contributions`: the **complete, ordered** list of contributions the document should
  have after the save.

### `parameters` shape

```json
{
  "contributions": [
    {
      "rank": "number | null",          // card position when ranking mode is on, else null
      "roles": ["string"],              // LoC relator URIs, e.g. http://id.loc.gov/vocabulary/relators/aut
      "person": {
        "uid": "string | null",         // null = brand-new person; graph mints/matches by identifiers
        "displayName": "string",
        "firstName": "string | null",
        "lastName": "string | null",
        "identifiers": [
          { "type": "string", "value": "string" }
        ]
      },
      "affiliations": [
        {
          "acronym":  "string | null",
          "name":     "string | null",
          "label":    "string | null",
          "type":     "string | null",  // e.g. "institution", "regrouplaboratory"
          "hal":      "string | null",  // identifier values per source
          "idref":    "string | null",
          "isni":     "string | null",
          "nns":      "string | null",
          "ror":      "string | null",
          "wikidata": "string | null"
        }
      ]
    }
  ]
}
```

Notes:
- `person.uid` is `null` for a brand-new person; the graph mints or matches by identifiers.
- An empty `contributions` array means "remove all contributors".

## Example message (anonymised)

The list mixes an internal person (referenced by uid), an external person (referenced by a source
identifier), and a brand-new person (`uid: null`):

```json
{
  "id": "00000000-0000-0000-0000-000000000001",
  "actionType": "UPDATE",
  "targetType": "DOCUMENT",
  "targetUid": "00000000-0000-0000-0000-0000000000aa",
  "path": "contributions",
  "personUid": "local-user1",
  "application": "sovisuplus",
  "timestamp": "2026-01-01T09:00:00.000Z",
  "parameters": {
    "contributions": [
      {
        "rank": null,
        "roles": ["http://id.loc.gov/vocabulary/relators/aut"],
        "person": {
          "uid": "local-user1",
          "lastName": "Doe",
          "firstName": "Jane",
          "displayName": "Jane Doe",
          "identifiers": [
            { "type": "orcid",     "value": "0000-0000-0000-0001" },
            { "type": "local",     "value": "user1" },
            { "type": "eppn",      "value": "user1@univ-example.fr" },
            { "type": "hal_login", "value": "jdoe" },
            { "type": "idhals",    "value": "jane-doe" }
          ]
        },
        "affiliations": [
          {
            "hal": "1000001", "nns": null, "ror": null, "isni": null,
            "name": "Example University - School of Law",
            "type": "regrouplaboratory",
            "idref": "100000001",
            "label": "Example University - School of Law [EU SL]",
            "acronym": "EU SL", "wikidata": null
          },
          {
            "hal": "1000002", "nns": null, "ror": null, "isni": null,
            "name": "Example Health Research Department",
            "type": "institution",
            "idref": null,
            "label": "Example Health Research Department [EHRD]",
            "acronym": "EHRD", "wikidata": null
          }
        ]
      },
      {
        "rank": null,
        "roles": ["http://id.loc.gov/vocabulary/relators/aui"],
        "person": {
          "uid": "sudoc-http://www.idref.fr/000000000/id",
          "lastName": null,
          "firstName": null,
          "displayName": "Martin, Paul (19..-....)",
          "identifiers": [
            { "type": "idref", "value": "000000000" }
          ]
        },
        "affiliations": []
      },
      {
        "rank": null,
        "roles": ["http://id.loc.gov/vocabulary/relators/ctb"],
        "person": {
          "uid": null,
          "lastName": "Durand",
          "firstName": "Claire",
          "displayName": "Claire Durand",
          "identifiers": [
            { "type": "orcid", "value": "0000-0000-0000-0002" }
          ]
        },
        "affiliations": [
          {
            "hal": "1000003", "nns": null, "ror": null, "isni": null,
            "name": "Example Institute",
            "type": "institution",
            "idref": null,
            "label": "Example Institute [EI]",
            "acronym": "EI", "wikidata": null
          }
        ]
      }
    ]
  }
}
```

---

## Integration logic (graph processing)

The message is decoded into a `Change` (`target_type=DOCUMENT`, `path=contributions`,
`action_type=UPDATE`, full list in `parameters`), persisted, then applied with **replace
semantics**: the document's contributions are reconciled to exactly the submitted list. The pieces
below are adapted from the per-action rules described in the issue, re-expressed for the full-state
message.

> New routing required: `ChangeProcessorFactory` currently handles `path` values `subjects`,
> `documentType`, `titles`, `abstracts`, and `action_type == "MERGE"` — there is **no**
> `contributions` branch. A new `DocumentContributionsChangeProcessor` must be created and registered
> in `ChangeProcessorFactory.get_processor` for `path == "contributions"`.

### Reconciliation (replace semantics)

For the target document, compute the desired contribution set from `parameters.contributions` and:

- create a `Contribution` for a person not yet contributing to the document;
- update the existing `Contribution` for a person already contributing;
- delete any existing `Contribution` of the document whose person is **absent** from the submitted
  list (the same effect as the per-action `REMOVE`).

The graph already has the building blocks used by the source-driven path
(`SourceContributorMappingService._update_contributions` →
`document_dao.create_contribution` + `document_dao.delete_contributions_not_in`); reuse the same
DAO operations rather than introducing a parallel mechanism.

### Person resolution (per contribution)

For each `contribution.person`:

- If `person.uid` is provided, use that existing `Person` node.
- If `person.uid` is `null`, match against existing persons by the provided `identifiers`; create a
  new **external** person if no match is found. A null-uid person may match **either** an external or
  an internal person — if it matches an internal person, resolve to that internal person (and the
  internal-person identifier/name freeze rule below then applies).

**Matching rules differ by person kind** because of how identifiers are currently stored in the
graph (see the model note below):

- **External persons** (`external: True`) are matched on their **source person identifiers**: find a
  person whose `SourcePersonIdentifier`s are *at least partially* compatible with the incoming
  `identifiers`.
- **Internal persons** (`external: False`) carry `AgentIdentifier`s and are matched on those.

When the incoming identifiers point to **two or more different `Person` nodes**, choose by **name
similarity** between the candidate persons and the submitted person name (reuse the existing
name-distance helpers in `SourceContributorMappingService`). The identifier(s) that pointed to the
**non-selected** person(s) are **unusable**: discard them — never write an identifier onto a person
it does not consistently belong to. **Do not add inconsistent identifiers to the graph.**

> Gap: no existing query does this. `person_dao.find_by_identifiers` /
> `find_person_by_identifiers.cypher` match **only** `AgentIdentifier`, return the **first** hit
> (`LIMIT 1`), and perform no conflict detection or disambiguation. External persons reach their
> source identifiers via `Person-[:RECORDED_BY]->SourcePerson-[:HAS_IDENTIFIER]->SourcePersonIdentifier`
> — a path that query never traverses. New matching logic/queries are required to: (a) match external
> persons through their `SourcePersonIdentifier`s with *partial* compatibility, (b) match internal
> persons through `AgentIdentifier`s, (c) return **all** candidate persons (not just the first) so the
> name-similarity tie-break and unusable-identifier discard can run.

### Identifier & name updates — internal vs external

This is governed by the current identifier model:

> Today, only **source** people carry identifiers (`SourcePersonIdentifier`). The graph does **not**
> compute "true" `AgentIdentifier`s from source people. `AgentIdentifier`s exist only on **internal**
> people. Because nothing else writes `AgentIdentifier`s on external people, this action may safely
> create them there without any concurrent-writer conflict.

- **Internal persons** (`external: False`): identifiers are **immutable** here. sovisuplus is **not**
  allowed to edit internal-people identifiers — **enforce this**: ignore the incoming
  `person.identifiers` entirely (no add / update / remove of `AgentIdentifier`s), and do not modify
  the internal person's `PersonName`. Only the **contribution** (roles, rank, affiliations) is
  written for an internal contributor.
- **External persons** (`external: True`): create missing `AgentIdentifier` nodes from the incoming
  `identifiers` and link them via `HAS_IDENTIFIER` — but only the **consistent** ones (any identifier
  discarded by the name-similarity disambiguation above must not be written). The external person's
  `display_name` may be set from the submitted name.

> Rationale: affiliations are a property of the *contribution* (the signature at publication time),
> not the person's current memberships — an internal author may have been affiliated elsewhere when
> the document was published, or list extra affiliations in their signature. Affiliations evolve over
> time; identifiers do not. Hence affiliations are always updatable, while internal-person
> identifiers are frozen.

### Contribution content

Each `Contribution` stores:

- `roles` — the LoC relator URIs from `contribution.roles`;
- `rank` — when a non-null rank is provided.

> Gap: `document_dao.create_contribution` and `create_contribution_to_document.cypher` currently set
> only `roles` (no `rank`). Storing `rank` requires extending that DAO method and query (and
> confirming the merged `Contribution` is meant to carry a `rank` property).

### Affiliation resolution

Affiliations carry authority identifiers (`hal`, `idref`, `ror`, `isni`, `nns`, `wikidata`) plus
`name` / `label` / `acronym` / `type`. They must be linked to `AuthorityOrganizationState` or
`AuthorityOrganizationRoot` using the **existing affiliation resolution algorithm** — no new
mechanism, and no duplicate `AuthorityOrganizationState` / `AuthorityOrganizationRoot` when matching
identifiers already exist. Affiliations are updatable for **both** internal and external persons.

**Resolve in-memory; do not persist anything in the source layer.** The existing harvested path
calls `SourceOrganizationService.get_cluster(uid)` to assemble a cluster of persisted
`SourceOrganization` nodes before resolving — but that step is only *input preparation*. The
resolution algorithm itself, `AuthorityOrganizationService.get_or_create_authority_organization`,
accepts a `List[SourceOrganization]` of **in-memory** objects and never reads `SourceOrganization`
nodes from the graph; de-duplication happens one layer down in
`_get_or_create_state_in_graph_by_identifier` → `get_states_with_compatible_identifiers`, which
matches against existing `AuthorityOrganizationState`s **by identifier**. No `SourceOrganization`
node is required for that guarantee.

Do **not** create `SourceOrganization` nodes for message affiliations, and do **not** fabricate a
`SourceContribution`/`SourceRecord` to host them:
- a `SourceContribution` only exists under a harvested `SourceRecord` (`create_source_contribution`
  `MATCH`es a `SourceRecord`); a user edit has none, so a persisted `SourceOrganization` would be an
  orphan and a fabricated source record would invent fake harvest provenance.
- the message already carries every authority identifier inline, so the "cluster" is simply the
  in-memory list — there is nothing to discover via `get_cluster`.

Per contribution:

1. Build **in-memory** `SourceOrganization` objects from `contribution.affiliations`:
   - `source = HAL`, `source_identifier = affiliation.hal` → uid `hal-<hal>` (matches how harvested
     HAL source orgs are keyed, so resolution converges on the same authority as the harvested one);
   - `name = affiliation.name` (fall back to `label`);
   - `type` mapped from the message `type` (`"institution"`, `"regrouplaboratory"`, …) onto
     `SourceOrganization.SourceOrganisationType`, defaulting to `ORGANIZATION` when unmapped;
   - `identifiers` = the non-null id fields (`idref`, `ror`, `isni`, `nns`, `wikidata`) as
     `SourceOrganizationIdentifier`s.
   - Defensive: if `affiliation.hal` is null (should not happen given the HAL autocomplete), fall back
     to another identifier as the source key, or skip the affiliation — never mint a uid with an
     empty source identifier.
2. `AuthorityOrganizationService.get_or_create_authority_organization(in_memory_orgs)` — resolves the
   list (by identifiers, else normalized name) to an `AuthorityOrganizationRoot` with its states,
   matching/merging existing authorities by identifier and creating them only when absent.
3. `SourceContributorMappingService._elect_authority_organizations_for_affiliation_statements(...)` —
   elects one target per root (a unique matching state, else the root).
4. `document_dao.update_contribution_affiliation_statements(contribution_id, targets)` — attaches the
   elected authority targets to the contribution.

The resolution/election logic itself must not be reimplemented. Note (harmless): resolved
`AuthorityOrganizationState.source_organization_uids` will record the `hal-<hal>` uids even though no
such `SourceOrganization` node exists — that is tracking metadata on the authority, not a dangling
graph edge.

### Entities left untouched on removal

Removing a contribution removes only the authorship relationship for this document. It must **not**
delete: `Person`, `PersonName`, `AgentIdentifier`, `AuthorityOrganizationState`,
`AuthorityOrganizationRoot`, or the `Document`.

---

## Supersession — only the latest contributions change is applied

A document accumulates one `Change` per save, so several `path=contributions` changes can pile up
over time. They are **full-state** snapshots, so only the **most recent** one is meaningful — it
already describes the complete desired contributor set; replaying the older ones is redundant and,
if applied out of timestamp order, could even produce a wrong transient state.

Rule: among the stored `path=contributions` changes for a document, **only the latest** (by
`timestamp`, tie-broken by uid) is applied — both at interactive time (it is newest by definition)
and on replay. Older contributions changes are **superseded**.

- **Do not delete** superseded changes. They are retained for a forthcoming sovisuplus feature that
  displays the document's modification history.
- **"Latest" is computed lazily**, at apply/replay time — by selecting the maximum-`timestamp`
  `path=contributions` change for the document. Superseded changes are **not** mutated or tagged: no
  `superseded` status is written, no extra writes when a new change arrives. The newest is simply
  chosen at read time; the older ones remain untouched in the graph as history.
- `ChangeService.apply_changes_to_node` (the replay path) must therefore, for the `contributions`
  path, select and apply **only** the most recent contributions change and **skip** the rest —
  rather than its current behaviour of replaying every stored change for the target. Changes on other
  paths (subjects, titles, abstracts, …) are unaffected by this rule and keep being applied as today.

## After applying the change

- The change is **persisted immediately** as a graph modification (not a temporary state) and must
  be **replayable** idempotently after a remerge via `apply_changes_to_node`.
- **No separate document recomputation is triggered** by this action. User actions are already
  reapplied at the end of a document recompute; recomputing again here would be redundant. The
  action only reconciles contributions and then signals the update.
- **Intended consequence — user edits pin the contributor list against future harvests.** Because the
  saved change is replayed (full-replace) after every recompute, a saved contributor list
  **overrides** source-derived contributions on each subsequent recompute: co-authors newly
  discovered by later harvesting will **not** appear until the user saves again. This follows directly
  from the full-state replace + replay design and is the accepted behaviour, not a bug.
- A single **"document updated"** event is emitted once the whole message has been applied (reuse the
  existing `document_updated` signal / outbound document-updated message — there is **no** dedicated
  "confirmation" message type). The payload does not need to carry the complete document; sovisuplus
  re-queries the GraphQL API to resync.

### Outbound `MessageMode` is set by the trigger context

The mode of the "document updated" event is decided by **how the change is being applied**, not by
the change itself:

- **Applied as it just arrived from sovisuplus** (the AMQP user-action is processed directly) →
  emit with `MessageMode.INTERACTIVE` → **interactive** queue.
- **Replayed during a recomputation from source records** (`apply_changes_to_node` after a remerge /
  harvesting) → emit with `MessageMode.BATCH` → **batch** queue.

The change content and graph effect are identical in both contexts; only the outbound queue differs.

> Implementation note: `ChangeService.apply_change` currently hardcodes
> `document_updated.send_async(..., mode=MessageMode.INTERACTIVE)`. That is correct only for the
> direct-from-AMQP path. The mode must be **threaded through** the apply path so that
> `apply_changes_to_node` (the replay path, invoked from document recompute) emits
> `MessageMode.BATCH` instead. Do not leave the mode hardcoded.
