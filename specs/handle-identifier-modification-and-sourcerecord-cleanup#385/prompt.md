# Handle identifier modification and SourceRecord cleanup

Issue: https://github.com/CRISalid-esr/crisalid-ikg/issues/385
Upstream workflow change (SoVisu+): `sovisuplus/specs/872-refactor-account-edition-workflow/prompt.md`

## Context

SoVisu+ has reworked its account-edition workflow (SoVisu+ #872): **an identifier value can
never be replaced in place** — a value change is always a **Remove** followed by an **Add**.
Authentication now only ever *confirms* an existing value (it fails if the identity provider
returns a different one). On the wire, every identifier change is a clean **add / remove /
update**:

| Event (SoVisu+ §5) | actionType | routing key | `parameters` |
|---|---|---|---|
| Add without authenticating | `ADD` | `task.people.person.add` | `{ identifier: { type, value, authenticated: false } }` |
| Add through authentication (was empty) | `ADD` | `task.people.person.add` | `{ identifier: { type, value, authenticated: true } }` |
| Authenticate existing (value unchanged) | `UPDATE` | `task.people.person.update` | `{ identifier: { type, value, authenticated: true } }` |
| Remove | `REMOVE` | `task.people.person.remove` | `{ type, value }` |

This has two consequences for the IKG middleware, and this spec covers both:

1. **Enforce the remove+add rule on the message-processing side.** IKG currently *replaces
   identifiers in place* (the `else` branches added in #393). Since value changes now arrive as
   Remove + Add, that logic must go; IKG must instead handle explicit **REMOVE** (new) and
   **UPDATE** (authenticate-only) actions and treat **ADD** as add-only.

2. **Handle the identifier-removal cleanup (issue #385).** When an identifier is removed, the
   harvested source-layer data that was keyed on that identifier must be cleaned up, and the
   affected `Document`s recomputed — messaged on the **interactive** queue for quick user
   feedback.

> Reconciliation with #385's original framing: the issue describes the trigger as "the *value*
> of an Identifier node changes." Under the new remove+add workflow there is no in-place value
> change — the value to clean up is delivered directly by the **REMOVE** message
> (`parameters: { type, value }`). We therefore trigger cleanup on removal and no longer need to
> diff old vs new values. Authentication that only flips `authenticated`/`validated` (value
> unchanged, the `UPDATE` action) must **not** trigger cleanup.

## Current state (what exists today)

- Inbound: `AMQPUserActionsMessageProcessor._process_unregistered_change`
  (`app/amqp/amqp_user_actions_message_processor.py:87-143`) handles only `FETCH` and person
  `ADD`. Person `ADD` calls `PeopleService.authenticate_identifier`. **There is no REMOVE or
  UPDATE identifier handling** — any other actionType for a PERSON target silently falls through
  and returns `None`.
- `PeopleService._authenticate_id_hal` (`people_service.py:196-230`) and `_validate_idref`
  (`:277-312`) **overwrite `identifier.value` in place** (lines 223 and 307). ORCID never
  overwrites (mismatch → raise).
- `HARVESTED_FOR` is `(SourceRecord)-[:HARVESTED_FOR]->(Person)` with properties
  `identifier_used_type` / `identifier_used_value`
  (`queries/create_source_record.cypher:53-57`). The lookup
  `SourceRecordDAO.get_source_record_uids_by_identifier_used(person_uid, type, value)`
  (`source_record_dao.py:146`, query `get_source_record_uids_by_identifier_used.cypher`) already
  returns exactly the records harvested under a given identifier.
- Harvesting path (confirmed):
  `(p:Person)<-[:HARVESTED_FOR]-(s:SourceRecord)-[:HAS_CONTRIBUTION]->(c:SourceContribution)-[:CONTRIBUTOR]->(sp:SourcePerson)<-[:RECORDED_BY]-(p)`
  (`RECORDED_BY` is `(Person)-[:RECORDED_BY]->(SourcePerson)`, `link_source_people_to_person.cypher:4`).
- Document ↔ source: `(Document)-[:RECORDED_BY]->(SourceRecord)`; reverse lookup
  `DocumentDAO.get_document_by_source_record_uid` (`get_document_by_source_record_uid.cypher`).
- Recompute: emit **`document_sources_changed`** (payload `document_uid`, optional `mode`) →
  `DocumentService.update_from_source_records` (`crisalid_ikg.py:133`), which self-deletes the
  Document when its source set becomes empty (`document_service.py:118-121`).
- Signals: `app/signals.py` has person signals but **no identifier-removed signal**; every
  person signal is wired only to outbound AMQP dispatch in `crisalid_ikg.py:210-220`.
- `MessageMode.INTERACTIVE` suffixes the outbound routing key with `.interactive`
  (`amqp_message_publisher.py:117-137`).

---

## Part A — Enforce remove+add on the message-processing side

### A1. Inbound action handling (`_process_unregistered_change`)

For `targetType == "PERSON"` with `path == "identifiers"`, branch on `actionType`:

- **ADD** — *add-only*. Read `parameters.identifier = { type, value, authenticated }`.
  - If the person already has an identifier of that `type` → **reject** (log + raise
    `ValueError`); do **not** replace. SoVisu+ guarantees remove-before-add, so this is a safety
    net, surfaced through the existing error-reporting path (#402).
  - Otherwise create the identifier, stamping flags per the mapping in **A2**, then resolve any
    internal/external collision on that `(type, value)` per **A5**.
- **UPDATE** — *authenticate/confirm existing, value unchanged*. The identifier of that `type`
  must exist and its stored value must equal the message value → stamp flags per **A2**. Value
  mismatch → raise (should not happen; value changes come as Remove+Add). **No cleanup** (value
  unchanged).
- **REMOVE** — read `parameters = { type, value }`; call `PeopleService.remove_identifier(...)`
  (A4) and emit the removal signal (Part B).

Extend `allowed_id_types` to include `IDHALI` alongside `ORCID`, `IDHALS`, `IDREF`.

### A2. Flag mapping (ADD / UPDATE)

Every manual identifier `ADD`/`UPDATE` from SoVisu+ is performed by a privileged user, so it is
**at least a validation**. Stamp the stored flags as follows:

- **idref** — always `validated=True`, never `authenticated` (idref has no authentication
  process). The message's `authenticated` flag is ignored for idref.
- **orcid / idhals / idhali** —
  - message `authenticated == true` → `authenticated=True` (⇒ `validated=True`,
    `authentication_date=timestamp`);
  - message `authenticated == false`/absent → `validated=True`, `authenticated=False`
    (a manual add/edit by a privileged user counts as validation, even without authentication).

The `validated`/`authenticated` model (`agent_identifiers.py:24-54`) and the
"authenticated ⇒ validated" invariant are unchanged; this mapping simply guarantees
`validated=True` on every manual write.

### A3. Drop replace-in-place in `PeopleService`

Rework the identifier operations so **no path ever mutates an existing identifier's `value`**:

- Remove the `else` replace-in-place branches in `_authenticate_id_hal` (`:219-226`) and
  `_validate_idref` (`:302-308`). Authentication/validation may only:
  - create a new identifier when none of that type exists (via ADD), or
  - stamp `authenticated`/`validated` flags (per A2) on an existing identifier **whose value
    already matches** (via UPDATE); a value mismatch is an error, never an overwrite.

### A4. New `PeopleService.remove_identifier(person_uid, identifier_type, value)`

- Load the person, drop the matching `PersonIdentifier` from `person.identifiers`, persist.
- Delete the `HAS_IDENTIFIER` edge to the `AgentIdentifier {type, value}` for this person, and
  delete the `AgentIdentifier` node **only if no other Person references it** (identifiers can be
  shared internal/external — cf. the collision fix). A targeted
  `remove_person_identifier.cypher` is needed (the existing `delete_person_identifiers.cypher`
  is keep-set based, used by the update path, not suitable for a one-off targeted remove).
- Emit the dedicated removal signal (Part B) with the removed `(type, value)` and
  `mode=INTERACTIVE`.

### A5. Collision with an existing external person (auto-detach, one-owner-per-identifier)

`AgentIdentifier` nodes are `MERGE`d on `(type, value)` (`create_person_identifiers.cypher:3`),
so adding an identifier to an **internal** person that already exists as an **external**
co-author's identifier does not create a new node — it adds a second `HAS_IDENTIFIER` edge, and
the node ends up owned by two persons. This is the collision addressed by #397, but #397's
re-point logic lives only in `ContributionUpdateService`; the identifier **ADD path does not go
through it**, so the ADD flow must resolve the collision itself.

**Decision: enforce one-owner-per-identifier at add time.** After the internal person acquires
the identifier, if any **external** person (`external:true`) owns the same
`AgentIdentifier {type, value}`, **detach the external `HAS_IDENTIFIER` edge(s)** so the internal
person becomes the sole owner. This is the #397 invariant, applied automatically and **scoped to
the one identifier just added** (not the global CLI sweep `clear_shared_identifiers`).

- **Reuse:** the same edge-only detach as
  `detach_external_shared_identifiers.cypher`, but parameterised by `(type, value)` (and keeping
  the internal owner). Author `detach_external_identifier_owner.cypher` — delete
  `(:Person {external:true})-[r:HAS_IDENTIFIER]->(:AgentIdentifier {type, value})` where the node
  is also owned by the internal person; return the detached count.
- **Kept intact (consistent with #397 scope):** the `AgentIdentifier` node (now owned only by the
  internal person), and the **external `Person` node** with its other identifiers, contributions,
  and source records. No person merge, no eager re-attribution.
- **Re-attribution of the external co-author's already-harvested records** to the internal person
  is **not** done eagerly here — it relies on the re-harvest that `update_person` already triggers
  via `publications_to_be_updated`: records re-harvested under the new identifier link to the
  internal person through `SourceContributorMappingService`. (The external person's *pre-existing*
  records are left to the normal replace-semantics self-heal; a full external→internal merge stays
  out of scope, as in #397.)

---

## Part B — SourceRecord cleanup on identifier removal (#385)

### B1. Dedicated signal

Add `person_identifier_removed = signal('person-identifier-removed')` to `app/signals.py`,
sent with payload `{ person_uid, identifier_type, identifier_value }` and `mode`.

- Sent by `PeopleService.remove_identifier` (interactive path) — and by any future value-change
  path — **only when an identifier value is actually removed**, never on an authenticate-only
  (`UPDATE`) flow.
- Connect it in `crisalid_ikg.py` (`_register_person_events`) to a new cleanup handler
  (recommended: a method on `SourceRecordService`, reusing its `SourceRecordDAO` wiring —
  e.g. `SourceRecordService.cleanup_harvested_data_for_identifier`). Keep the existing outbound
  `dispatch_person_updated` wiring separate; this new connection drives the graph cleanup.

### B2. Cleanup algorithm

1. `source_record_uids = get_source_record_uids_by_identifier_used(person_uid, type, value)`
   (existing query) — the exact records harvested under the removed identifier.
2. `affected_document_uids = ∪ get_document_by_source_record_uid(uid)` for those records —
   **captured before any deletion** (the `Document -[:RECORDED_BY]-> SourceRecord` edge is
   severed by a Case-1 delete).
3. For each `SourceRecord`, count its remaining `HARVESTED_FOR` relationships:
   - **Case 1 — exclusive** (this is the only `HARVESTED_FOR`): delete the `SourceRecord`, its
     `SourceContribution` nodes, and the `HARVESTED_FOR` relationship; delete each
     `SourcePerson` **only if it is not a CONTRIBUTOR of any other `SourceContribution`** (i.e.
     not linked to another `SourceRecord`); delete this person's `RECORDED_BY` edge to those
     `SourcePerson`s. **Preserve** `SourceJournal`, `SourceIssue`, and `SourceOrganization`
     (all `MERGE`d and shared across records).
   - **Case 2 — shared** (other `HARVESTED_FOR` remain): delete **only** this person's
     `HARVESTED_FOR` relationship and its `RECORDED_BY` edge to the `SourcePerson` (if present).
     Keep the `SourceRecord`, `SourceContribution`, `SourcePerson`, and every harvesting path of
     the other persons untouched.
4. **No orphans**: after cleanup no `SourceContribution` or `SourcePerson` may exist outside a
   harvesting path.
5. For each `document_uid` in `affected_document_uids`, emit `document_sources_changed`
   (`mode=INTERACTIVE`) → `DocumentService.update_from_source_records`. This recompute is
   **required in both cases** and is *not* a no-op for shared records:
   - **Case 1** — the deleted `SourceRecord` drops out of the document's source set; the document
     is recomputed from the remaining sources, and `DocumentService` self-deletes it if it now
     has none (`document_service.py:118-121`).
   - **Case 2** — the document's source **set** is unchanged (the shared record survives), but the
     recompute re-derives contributions via
     `SourceContributorMappingService.update_contributions()`. Because Case 2 removed the person's
     `HARVESTED_FOR` **and** `RECORDED_BY → SourcePerson` and the identifier is gone, none of the
     three matching strategies (`_match_by_identifiers` / `_match_by_name` /
     `_match_with_external_person`) map that `SourcePerson` back to the removed person, so
     `delete_contributions_not_in` **prunes the removed person's stale Contribution** to the
     document. The document survives; only that person's contribution is dropped, other persons'
     contributions untouched. **This disassociation is the whole point of recomputing shared
     records** — it must not be skipped as "idempotent".

### B3. New Cypher (to author) — reuse existing primitives where possible

- `remove_person_identifier.cypher` (A4) — targeted `HAS_IDENTIFIER`/node removal.
- A count/guard query for remaining `HARVESTED_FOR` on a record (Case 1 vs Case 2).
- `delete_exclusive_source_record.cypher` — Case 1: delete `SourceRecord` +
  `SourceContribution`s + orphan `SourcePerson`s + `HARVESTED_FOR`, preserving shared entities.
  (`delete_source_record_contributions.cypher` deletes a record's contributions and can be
  reused as a building block.)
- `detach_shared_harvested_for.cypher` — Case 2: delete one `HARVESTED_FOR` + the person's
  `RECORDED_BY` to the record's `SourcePerson`(s).
- `detach_external_identifier_owner.cypher` (A5) — detach the external `HAS_IDENTIFIER` edge for
  one `(type, value)` when an internal person also owns it.

Guard every deletion so it cannot touch another person's harvesting path (scope by
`person_uid` + the specific `source_record_uid`).

---

## Affected code

- `app/amqp/amqp_user_actions_message_processor.py` — REMOVE/UPDATE branches; add-only ADD;
  `allowed_id_types` += `IDHALI`.
- `app/services/people/people_service.py` — drop replace-in-place; add `remove_identifier`;
  split authenticate vs add semantics; auto-detach an external owner on ADD (A5).
- `app/services/source_records/source_record_service.py` (+ `source_record_dao.py`) — new
  `cleanup_harvested_data_for_identifier` + DAO delete methods.
- `app/signals.py` — `person_identifier_removed`; `app/crisalid_ikg.py` — wire it to the
  cleanup handler.
- `app/graph/neo4j/queries/` — the new Cypher files above.

## Tests

- **Message processing**: REMOVE triggers `remove_identifier` + the signal; ADD is add-only
  (rejects an existing type); UPDATE authenticates without value change and emits **no** cleanup
  signal; no code path overwrites an identifier value.
- **Collision on ADD (A5)**: adding to an internal person an identifier already owned by an
  external person leaves the `AgentIdentifier` owned **only** by the internal person (external
  `HAS_IDENTIFIER` edge detached); the external `Person` node and its other data survive; no
  second-owner edge remains.
- **Cleanup Case 1** (exclusive record): `SourceRecord` + `SourceContribution` gone; orphan
  `SourcePerson` gone; shared `SourcePerson`/`SourceJournal`/`SourceOrganization` preserved;
  linked `Document` recomputed (or deleted when it loses its last source).
- **Cleanup Case 2** (shared record): only this person's `HARVESTED_FOR` + `RECORDED_BY` removed;
  the record and every other person's path intact; after recompute the removed person's
  `Contribution` to the shared `Document` is **gone** while the other persons' contributions to
  that same document remain.
- **No orphans**: post-cleanup assertion that no `SourceContribution`/`SourcePerson` exists
  outside a harvesting path.
- **Trigger discipline**: an authenticate-only `UPDATE` (value unchanged) performs **no**
  source-record cleanup.
- **Messaging**: affected-document events are emitted on the **interactive** routing key.

## Verification

Neo4j test instance running (per CLAUDE.md). Build a fixture graph with (a) a person + an
exclusive harvested record and (b) a record shared by two persons, then drive a REMOVE message /
call the service and assert the graph state and emitted document events. `APP_ENV=TEST pytest`,
then `pylint --rcfile=.pylintrc app/` (no score regression).

## Out of scope

- The SoVisu+ side (UI controls, permission matrix, callbacks) — SoVisu+ #872.
- A first-class stored `authenticated` schema change beyond the existing `validated`/
  `authenticated` fields.
- Cleanup for unregistered/`FETCH` flows and for non-identifier person updates.
