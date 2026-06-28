# Fix internal/external author identifier collision

## Context

A sovisuplus contribution-update message (see
`specs/handle-contribution-update-message-from-sovisuplus#391/prompt.md`) carries, for each
contributor, a `person` block with an `identifiers` list. For **external** persons these identifiers
are minted as `AgentIdentifier` nodes by `ContributionUpdateService` — this is by design: a user
performs a manual alignment in the sovisuplus *Authors* tab, and the resulting identifier
(e.g. an `idhals`, `idref`, `orcid`) is attached to the external co-author.

The problem appears when the **same identifier already belongs to an internal person**. Because an
`AgentIdentifier` is a unique join key (composite uniqueness constraint on `(type, value)`), the
graph holds **exactly one node** per `(type, value)`. Linking it to a second person does not create a
new node — it adds a second `HAS_IDENTIFIER` edge to the *existing* node. The identifier then has two
owners.

### Observed case

An external co-author **"Lamy, Jérôme"** (`scanr-anon:doi10.4000/chrhc.16724:lamy-jerome`,
`external: True`) and the internal person **"Jerôme Lamy"** (`local-jelamy`, `external: False`) share
three `AgentIdentifier` nodes:

| type     | value                  |
|----------|------------------------|
| `idhals` | `jerome-lamy`          |
| `idref`  | `116365803`            |
| `orcid`  | `0000-0003-3820-284X`  |

These are the same human. The alignment in sovisuplus is correct, but sovisuplus enforces that an
identifier belongs to a single person, so when it tries to (re)assign `idhals=jerome-lamy` it is
**refused — the identifier is already attributed to someone else** (the internal person, via the edge
the graph wrongly created).

### Root cause

`ContributionUpdateService._resolve_person`
(`app/services/contributions/contribution_update_service.py`) has two branches:

- the **null-uid** branch (`_match_or_create_person`) computes `_inconsistent_identifier_keys` and
  discards identifiers that point to a different person before writing;
- the **uid-provided** branch (lines ~99–104) calls `_apply_identifier_policy(..., set())` with an
  **empty** inconsistent-key set — i.e. **no conflict detection at all**.

When a message references the external person by uid and carries the aligned identifiers, the uid
branch writes *all* of them via `add_person_identifiers` → `create_person_identifiers.cypher`, which
`MERGE`s each `AgentIdentifier` on `(type, value)`. The nodes already exist (owned by the internal
person), so MERGE re-uses them and adds a second `HAS_IDENTIFIER` edge from the external person. That
is the collision.

> Note: external persons legitimately carry `AgentIdentifier`s (this is the #391 design). The bug is
> **not** "external persons have identifiers" — it is "a single `AgentIdentifier` node is owned by two
> different `Person` nodes." The invariant to enforce is one-owner-per-identifier.

## Desired behaviour

**An incoming identifier already owned by an existing person — via an `AgentIdentifier`, internal or
external — means the contributor *is* that person.** Honour the alignment by resolving the
contribution to the owning person, instead of copying the identifier onto a second person and creating
a shared node.

### Resolution rule (`_resolve_person`)

For each contribution, regardless of whether `person.uid` is an external uid, an internal uid, or
`null`:

1. Look up the owners of the incoming identifiers (`find_candidates_by_identifiers` — already returns
   all candidate persons with the matching identifier and their `external` flag).
2. **If an incoming identifier is owned (via `AgentIdentifier`) by an existing person → re-point *this
   contribution* to that owning person**, whether internal or external. The owning person — not the
   uid carried in the message — becomes the contribution's person.
   - **Precedence:** if both an internal and an external owner match, the **internal** person wins.
   - **Tie-break:** among candidates of the selected kind, pick by name similarity between the
     candidate and the submitted `displayName` (reuse `_select_by_name_similarity`).
   - **Owner is internal** → apply the internal-person **freeze** policy: ignore the incoming
     `identifiers` (no add / update / remove of `AgentIdentifier`s) and do **not** modify the internal
     person's `PersonName`. Only the contribution (roles, rank, affiliations) is written.
   - **Owner is external** → resolve to that external person and apply the normal external policy:
     merge the **other consistent** incoming identifiers onto it (`MERGE`), `display_name` may be set
     from the submitted name. This consolidates duplicate external co-authors onto one node instead of
     spawning a new one.
3. **Otherwise** (no `AgentIdentifier` owner) keep the current behaviour: resolve to the external
   person (existing uid, or matched/created external person), and write only the **consistent**
   incoming identifiers — any identifier owned by a *different* person is discarded
   (`_inconsistent_identifier_keys`).

> **Match on `AgentIdentifier` ownership, not on `SourcePersonIdentifier`.** Re-pointing is driven by
> `AgentIdentifier`s only — those are authoritative, minted by a deliberate manual alignment. The
> fuzzier `SourcePersonIdentifier` *partial-compatibility* match (used elsewhere to match external
> persons) must **not** trigger a re-point: a weak harvested-source-id overlap between two genuinely
> distinct external co-authors would otherwise collapse them onto the same contribution. Source-id
> conflicts stay in the discard-on-conflict case (step 3).

This makes conflict detection apply to **both** branches: the uid-provided branch must no longer pass
an empty inconsistent-key set, and must re-point exactly like the null-uid branch.

### Scope — strictly per-contribution

- Do **not** merge or delete the external `Person` node. It remains a valid co-author signature on any
  document where it has not been aligned.
- Do **not** move the external person's other contributions.
- Do **not** clean up orphaned external persons. If re-pointing leaves an external person with no
  contributions, that is acceptable — orphan cleanup is out of scope.
- The external person never receives an internal person's identifier (that is exactly what created the
  collision).

### Self-healing going forward

Reconciliation is full-state / replace semantics, so no special migration is needed for *future*
saves: the next time sovisuplus sends the contribution list for a document, `_resolve_person` returns
the internal person, `document_dao.create_contribution` creates the internal contribution, and
`document_dao.delete_contributions_not_in` drops the stale external one.

## One-shot data cleanup — clear existing shared identifiers

The code fix prevents *new* collisions but does not remove the `HAS_IDENTIFIER` edges already created.
Provide a one-shot cleanup that **detaches every `AgentIdentifier` shared between an external and an
internal person from the external person**, leaving it owned solely by the internal person.

- Target: every `(:Person {external:true})-[r:HAS_IDENTIFIER]->(:AgentIdentifier)<-[:HAS_IDENTIFIER]-(:Person {external:false})`.
  Delete the relationship `r` (the external person's edge). Do **not** delete the `AgentIdentifier`
  node (the internal person still owns it) and do **not** delete the external `Person`.
- This restores one-owner-per-identifier and lets sovisuplus re-assign the aligned identifier.
- Existing contributions that still point at the external person are **not** re-pointed by the cleanup;
  they will be corrected on the next sovisuplus save (replace semantics) per the rule above.
- Identify-only first: the cleanup should report which `(external_person, identifier, internal_owner)`
  triples it will change before applying, for auditability.

> Currently exactly **one** external person is affected (the Lamy case, 3 shared identifiers), all of
> the external↔internal kind, but the cleanup must sweep the general pattern, not hard-code that
> person.

> **External↔external shared nodes** (an `AgentIdentifier` owned by two *external* persons) do **not**
> exist in the current data and are **out of scope** for the cleanup: there is no canonical owner to
> keep, so detaching one side blindly is unsafe. Such cases (should any arise) are resolved by the
> re-point rule on the next sovisuplus save, which consolidates onto a single external person.

## Out of scope

- Person merge / deduplication as a general facility (none exists; `EquivalenceService` is
  source-record only).
- Orphan-external-person deletion.
- Any change to how external persons acquire identifiers in the non-colliding case (#391 behaviour is
  correct).

## Acceptance

- A contribution-update message that carries an identifier owned by an internal person attaches the
  contribution to the **internal** person; no identifier is written onto the external person; the
  internal person's identifiers and name are untouched.
- The uid-provided branch performs the same conflict detection as the null-uid branch.
- After the one-shot cleanup, no `AgentIdentifier` node is linked to more than one `Person`.
- The external `Person` node and its other contributions are left intact.