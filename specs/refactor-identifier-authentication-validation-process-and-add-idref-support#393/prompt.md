# Refactor identifier authentication/validation process (and add IdRef support)

Issue: https://github.com/CRISalid-esr/crisalid-ikg/issues/393

## Context

Currently, only `hal` and `orcid` identifiers can be marked as **authenticated** when a user links their account in SoVisu+. This authentication sets `authenticated: true` and `authentication_date` on the corresponding `AgentIdentifier` node.

`idref` identifiers do not have a real authentication process (no account linking), but superusers (librarians, for instance) in SoVisu+ will be able to **validate** them manually.

This issue covers two things:

1. A general refactor of the identifier authentication/validation process to introduce a shared `validated` concept across all identifier types.
2. The addition of a validation process for `idref` identifiers specifically, built on top of that refactor.

## Terminology

* **Validated**: a generic property applying to *all* identifier types (`hal`, `orcid`, `idref`, ...), indicating the identifier has been confirmed as correct/legitimate (whether by real authentication or manual validation).
* **Authenticated**: a stronger, more specific status that only applies to identifiers with a real authentication process (currently `hal` and `orcid`), obtained via account linking.

## Implementation rules

### 1. General refactor — validation for all identifiers

* Every identifier type must be able to be marked as `validated: true` on its `AgentIdentifier` node.
* The `authenticated` property and `authentication_date` remain specific to `hal` and `orcid`, since only those have a real authentication process. Other identifier types must not set these two properties.
* When `hal` or `orcid` are authenticated, they must also be marked as `validated: true` (authentication implies validation).

### 2. IdRef validation

* The logic from the `hal` authentication can be replicated as-is, adapted to only set validation (no authentication).
* The validation reacts to `ADD` messages, similar to the ones used for authentication of `orcid` or `hal` identifiers.
* When an `idref` identifier is validated via an `ADD` contribution message, the corresponding `AgentIdentifier` node must be created/updated with:
  * `validated: true`
  * *(no* `authenticated`* or* `authentication_date`* properties, since* `idref`* has no real authentication process)*
* A Person can only have one `AgentIdentifier` node of type `idref`. This invariant is **not** enforced in Neo4j — the `MERGE` in `create_person_identifiers.cypher` is keyed on `(type, value)`, so the DB would tolerate two same-type nodes with different values. It is upheld only in Python by `Person.get_identifier` (returns one per type) and `Agent._deduplicate_identifiers` (keeps the last per type). The `idref` flow must respect the same layering.

### Collision behaviour (existing `idref` of a different value)

Mirror the `hal` authentication path (`_authenticate_id_hal`), **not** the `orcid` one:

* If the Person has no `idref` yet → create the node with `validated: true`.
* If the Person already has an `idref` with a **different** value → **replace in place**: overwrite `value` and set `validated: true`. (This is HAL's behaviour; `orcid` instead aborts on a value mismatch — `idref` does *not* follow that.)
* If the Person already has an `idref` with the **same** value that is already `validated` → raise (`ValueError`, "already validated"), matching HAL's "already authenticated" guard.

Cleanup of the replaced/old identifier value (and any orphaned `AgentIdentifier` node left behind after an in-place replacement) is handled by the value-list keep/delete logic in `PersonDAO._update_person_transaction`, and will be revisited by a **later spec** that introduces a dedicated identifier-deletion process and its related concerns. This spec only needs the replace-in-place semantics above.

## Affected code

- **`app/models/agents.py` (`AgentIdentifier` / `PersonIdentifier`)** — add a strict `validated: bool = False` field and make `authenticated: bool = False` a strict non-nullable boolean too (both default `false`). Add/extend a validator so that `authenticated is True` forces `validated = True` (authentication implies validation) regardless of the call path.
- **`app/graph/neo4j/queries/create_person_identifiers.cypher`** — the `MERGE` currently sets `authenticated` / `authentication_date` only. Add `validated` handling in both `ON CREATE SET` and `ON MATCH SET`, mirroring the existing `CASE` pattern (default to `NULL`/preserve when the incoming value is absent).
- **`app/graph/neo4j/person_dao.py` (`_update_person_transaction`)** — the delete keep-set is currently built from identifiers where `not identifier.authenticated`. Confirm this still preserves a `validated`-but-not-`authenticated` `idref` across updates. Since `idref` is not authenticated it is included in the keep-set (protected), and an in-place value replacement drops the old value node's relationship because the old value is no longer in the incoming list — this is the intended behaviour, but it should be verified with a test.
- **`app/services/people/people_service.py`** — `authenticate_identifier` dispatches only for `IDHALI`/`IDHALS`/`ORCID`. Add an `idref` branch (a `_validate_idref` mirroring `_authenticate_id_hal`, but setting only `validated=True`, never `authenticated`/`authentication_date`). Consider renaming the public entry point to reflect that it now covers validation as well as authentication.
- **`app/amqp/amqp_user_actions_message_processor.py` (`_process_unregistered_change`, `ADD` branch)** — `allowed_id_types` is `[ORCID, IDHALS]`. Add `IDREF` so `ADD` messages for `idref` reach the service.

## Inconsistencies / points to resolve

1. **Property name casing** — the original issue text writes `authenticationDate` (camelCase) in the `idref` section but `authentication_date` in the general rules. The Neo4j node property is `authentication_date` (snake_case); this spec uses that form throughout.
2. **"Every identifier type must be able to be marked as `validated`" vs. the actual flow** — the *data model* change makes `validated` available on every `AgentIdentifier`, but the only mechanism that sets it (the `ADD` user-action message) is restricted to `hal`, `orcid`, and now `idref`. There is no generic "validate any identifier" flow. If that is intended, the general refactor is a data-model + `hal`/`orcid`/`idref` change only; other types can carry `validated` but nothing currently sets it. Flag this so no one expects validation UI for arbitrary types.
3. **`hal` (replace) vs `orcid` (abort) collision asymmetry** — these two "authenticated" types already behave differently on a value mismatch. `idref` deliberately follows `hal` (replace), so "replicate the authentication logic" must be read as "replicate `_authenticate_id_hal`", not the `orcid` path.
4. **`validated` and `authenticated` are strict booleans defaulting to `false`** (resolved). Both properties are non-nullable `bool` with default `false` on the model. The `authenticated` tri-state (`true`/`false`/`NULL`) that the current Cypher produces is dropped: replace the `ELSE NULL` branches in `create_person_identifiers.cypher` (`ON CREATE`) with `ELSE false`, and set `validated` the same way. `authentication_date` stays nullable (only meaningful when `authenticated = true`). Since `_update_person_transaction` deletes-and-recreates identifier relationships on every person update, existing `NULL` values are normalised to `false` on the next write; add a one-off migration only if a query relies on the boolean being present before the next update.