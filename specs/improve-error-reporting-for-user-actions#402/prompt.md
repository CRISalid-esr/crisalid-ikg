# Improve error reporting and error recording for user actions

Issue: https://github.com/CRISalid-esr/crisalid-ikg/issues/402

## Context

When a user action arrives on the user-actions queue, `AMQPUserActionsMessageProcessor`
builds a `Change` and hands it to `ChangeService.create_and_apply_change`, which persists the
change, applies it through a change processor, and — on success — emits `document_updated`.
The resulting outbound `event.documents.document.updated.interactive` message is what lets
sovisuplus (where the action originated and where the edited data is frozen in the meantime)
refresh its view and notify the user.

Today the feedback loop only works for the happy path. Errors fall into two buckets, and
neither reaches the user:

### 1. Hard failures — change not applied, no outbound message at all

`ChangeService.apply_change` catches `DatabaseError` / `ValueError`, sets
`Change.status = FAILED`, stores `error_message` on the `Change` node, logs, and re-raises.
The exception propagates to `AMQPMessageProcessor.wait_for_message`, the inbound message is
nacked, and **nothing is published back**. Sovisuplus never learns the action failed; the
frozen data stays frozen until some timeout or manual refresh.

Additional hard-failure paths that never even reach a `Change` node:

- `Change.model_validate` fails in `_process_registered_change` → `ValueError`, logged only;
- `ChangeService.create_change` raises `ValueError` when the target document does not exist —
  the change is not persisted, so there is not even a FAILED node recording the attempt.

### 2. Partial failures — change "applied", losses silently swallowed

During a full-state contribution update (`ContributionUpdateService.reconcile`, issue #391),
several per-item problems are logged and skipped without affecting the change status:

- `logger.warning("Skipping contribution with unresolvable person: {}", person)` —
  the contribution is dropped from the reconciled list
  (`app/services/contributions/contribution_update_service.py:65`);
- `logger.error("Could not create external person {}: {}", display_name, error)` —
  `ConflictError` / `ValueError` on external-person creation; contribution dropped
  (`contribution_update_service.py:258`);
- `logger.warning("Cannot create external person without a display name")` — contribution
  dropped (`contribution_update_service.py:246`);
- `logger.error("Conflict error while resolving affiliation {}: {}", ...)` — affiliation
  silently missing from the contribution (`contribution_update_service.py:296`);
- `logger.warning("Affiliation without usable identifier skipped: {}", affiliation)` —
  affiliation silently dropped (`contribution_update_service.py:312`).

Because `reconcile` has **replace semantics**, a skipped contribution is not merely "not
added" — it is **removed** from the document if it existed before
(`delete_contributions_not_in`). The change is then marked `APPLIED`, `document_updated`
fires, and sovisuplus refreshes a document that silently lost an author the user just typed
in. This is the worst case: the user gets positive feedback ("saved") for a partially
destructive outcome.

## Goal

1. **Record** — every error or per-item warning produced while applying a user action must be
   persisted on the `Change` node, not just logged.
2. **Report** — the outcome (success / partial success / failure), with its errors and
   warnings, must be emitted as a RabbitMQ message that sovisuplus can consume to unfreeze
   the UI and notify the user.
3. **Correlate** — the outbound message must let sovisuplus identify which action and which
   user it concerns: the change uid (`application:id` — sovisuplus minted the `id`, so it can
   correlate directly), the acting user (`person_uid`), and the target (`target_uid`).

**Scope: registered document changes only.** The unregistered actions
(`FETCH`, person-`ADD` in `_process_unregistered_change`) have no `Change` node; their error
reporting is tracked separately.

## Design

### A. Two dedicated outbound change events

Two new outbound event messages, `change.applied` and `change.failed`, report the outcome of
a user action. The existing document-updated message stays exactly as it is: it remains the
generic "data changed, resync" signal (it is emitted from many contexts — batch recompute,
merges, CLI — and on hard failure it is not emitted at all, so it cannot carry outcome
reports). The new change events are the "your action was processed, here is the outcome"
signal. On success sovisuplus receives both; on failure only `change.failed`.

**Change events are emitted only in interactive mode** — i.e. when the change is applied
directly from the sovisuplus user-action message (`MessageMode.INTERACTIVE`). Batch replays
stay silent toward clients (see section G).

### B. Message contract

Routing keys (graph exchange; the publisher appends the mode suffix, which is always
`interactive` here):

```
event.changes.change.applied.interactive
event.changes.change.failed.interactive
```

New settings: `amqp_graph_change_event_applied_routing_key` /
`amqp_graph_change_event_failed_routing_key` (pattern of the existing
`amqp_graph_document_event_*_routing_key` settings).

Payload:

```jsonc
{
  "type": "change",
  "event": "applied | failed",
  "fields": {
    "uid": "sovisuplus:0000-...-0001",     // Change uid = application:id
    "id": "0000-...-0001",                 // the application-scoped id, echoed back
    "application": "sovisuplus",
    "person_uid": "local-user1",           // the user who performed the action
    "target_type": "DOCUMENT",
    "target_uid": "00000000-...-00aa",
    "path": "contributions",
    "action_type": "UPDATE",
    "status": "applied | failed",
    "error_message": "string | null",      // hard failure cause (status=failed)
    "warnings": [                          // per-item losses (may be non-empty on applied)
      {
        "code": "UNRESOLVABLE_PERSON",
        "message": "Skipping contribution with unresolvable person",
        "context": { "display_name": "Claire Durand" }
      }
    ],
    "timestamp": "2026-01-01T09:00:00Z"    // when the outcome was recorded
  }
}
```

Notes:

- `event: applied` with a non-empty `warnings` array is the "partial success" case —
  sovisuplus can show *"saved, but 1 contributor could not be resolved"*.
- The payload deliberately does **not** carry document data; sovisuplus resyncs through the
  existing document-updated message / GraphQL as today.
- No document lookup is needed to build the payload — everything comes from the `Change`
  node — so the factory is trivial and works even when the target document is broken.
- `warnings[].context` echoes user-submitted data (names, identifiers) for display; there is
  no message-size constraint on the graph exchange.

#### Warning taxonomy (initial)

| code | source | context fields |
|---|---|---|
| `UNRESOLVABLE_PERSON` | contribution skipped, person could not be resolved | `display_name`, `identifiers` |
| `EXTERNAL_PERSON_CREATION_FAILED` | `ConflictError`/`ValueError` on person create | `display_name`, `error` |
| `MISSING_DISPLAY_NAME` | external person without display name | `identifiers` |
| `AFFILIATION_CONFLICT` | `ConflictError` on authority resolution | `source_organization_uid`, `error` |
| `AFFILIATION_WITHOUT_IDENTIFIER` | affiliation with no usable identifier | `affiliation` |

The taxonomy is open — codes are plain strings in the message contract; new processors add
their own codes.

### C. Collecting warnings — a change application report

Change processors currently return `None` from `apply()` and services log-and-continue.
Introduce a small report object threaded through the apply path:

- `ChangeApplicationReport` (new model, e.g. `app/models/change_report.py`): a list of
  `ChangeWarning(code, message, context: dict)` entries.
- `AbstractChangeProcessor.apply()` returns a `ChangeApplicationReport` (empty list = clean
  success). Existing processors return an empty report unchanged.
- `ContributionUpdateService.reconcile(...)` accepts/returns the report and **appends a
  warning at every point where it currently logs and skips** (the five sites listed above).
  Logging stays; the report is additional, not a replacement.
- `ChangeService.apply_change`:
  - on success: persist the report on the `Change` node (see D), then — in interactive mode —
    emit `change.applied`, and emit the existing `document_updated` as today;
  - on failure: persist status + `error_message` as today, then — in interactive mode —
    emit `change.failed` before re-raising.

### D. Safety guard — an all-skipped reconcile is a hard failure

If the submitted contribution list is **non-empty** but every contribution was skipped (the
resolved list ends up empty), `ContributionUpdateService.reconcile` must **raise** instead of
proceeding — otherwise `delete_contributions_not_in` would wipe every contributor from the
document on the strength of a fully-failed resolution. The raised error follows the hard
failure path: `status=FAILED`, `error_message` set, `change.failed` emitted, previous graph
state untouched. An intentionally empty submitted list ("remove all contributors") is still
applied as before.

### E. Recording on the Change node

Extend the `Change` model and Cypher queries:

- `Change.warnings: list[ChangeWarning]` (default `[]`), marshalled to a JSON string for
  storage (same pattern as `parameters` / `marshal_parameters`), property `warnings` on the
  node;
- `update_change_status.cypher` and `create_document_change.cypher` set `warnings` alongside
  `status` / `error_message`;
- `ChangeDAO._hydrate` unmarshals it (a `field_validator` on the model, mirroring
  `_unmarshal_parameters`).

No new status value: `status=applied` + non-empty `warnings` **is** the partial-success case;
the replay logic (`create_and_apply_change` checks `status == APPLIED`) stays simple.

### F. Signal wiring

Follow the existing pattern (`app/signals.py` → `CrisalidIKG.__init__` →
`AMQPInterface` → factory):

- two new signals: `change_applied = signal('change-applied')` and
  `change_failed = signal('change-failed')` — matching the created/updated/deleted
  granularity used everywhere else, and letting sovisuplus bind failure handling to its own
  queue if desired;
- `ChangeService` sends them with `change=<Change>` (interactive mode only);
- `AMQPInterface.dispatch_change_applied / dispatch_change_failed` → new
  `AMQPChangeEventMessageFactory` (payload built purely from the `Change` object passed in
  the signal — unlike the document factories, no DB round-trip);
- register the new `EventMessageSubtype.CHANGE_APPLIED / CHANGE_FAILED` in
  `AMQPMessagePublisher`.

### G. Failures that occur before a Change exists

Two pre-persistence failures currently leave no trace:

1. **Validation failure** (`Change.model_validate` raises) — we cannot build a `Change`, but
   the raw payload still carries `id`, `application`, `personUid`, `targetUid`. Emit a
   `change.failed` event built from those raw fields with
   `error_message = "invalid message: ..."`. No `Change` node is written (nothing valid to
   write).
2. **Target does not exist** (`create_change` raises `ValueError`) — the `Change` object
   exists in memory; set `status=FAILED` + `error_message` and emit `change.failed`. The node
   is **not** persisted: it cannot be linked to the missing document via `HAS_CHANGE`, and an
   unlinked node would pollute the graph — the emitted event + logs are the record.

Practically this means `AMQPUserActionsMessageProcessor._process_registered_change` (or
`create_and_apply_change`) gains a try/except that guarantees a `change.failed` event on any
`ValueError`/`DatabaseError`, instead of letting the exception silently die in the worker
loop.

### H. Batch replay (`apply_changes_to_node`)

Replayed changes (after a document remerge) go through the same `apply_change`, but with
`MessageMode.BATCH`: **no change event is emitted** — batch replays stay silent toward
clients. `apply_changes_to_node` continues to swallow exceptions per change (one bad change
must not block the others), and each failure still updates `status` / `error_message` /
`warnings` on the `Change` node, so the outcome remains recorded in the graph.

## Included fix

`ChangeService.create_and_apply_change` has a pre-existing bug: when
`existing.status == FAILED` it logs *"Retrying."* and then `return`s without retrying
(`change_service.py:38-40`). Fix it here — the retry must clear `error_message` / `warnings`
before re-applying, which interacts directly with this feature.

## Out of scope

- Unregistered actions (`FETCH`, person-`ADD`): no `Change` node, errors still vanish;
  tracked separately.
- The sovisuplus side (consuming the new events, unfreezing, toasting the user, displaying
  warnings) is a separate spec in the sovisuplus repo.
