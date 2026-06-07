# Separate batch/interactive messages — 5th routing-key segment

## Context

The CRISalid bus adopts a new convention: every routing key gains a **5th segment** `.interactive`
or `.batch` that declares the traffic class of the message.

sovisuplus has already implemented its side (issue #827):
- It publishes task messages with the `.interactive` suffix and subscribes to two separate queues
  (`sovisuplus-interactive` / `sovisuplus-batch`) using wildcard bindings `event.*.*.*.interactive`
  and `event.*.*.*.batch`.
- `definitions.sample.json` in `crisalid-deployment` has already been updated accordingly.

This issue implements the **crisalid-ikg** side:

1. Rename/replace the inbound user-actions queue to `crisalid-ikg-actions-interactive` and update
   its binding keys to the new 5-segment format.
2. Add a **mode** (`batch` or `interactive`) to all outbound messages published on the `graph`
   exchange and on the `publications` exchange.
3. Fix the harvesting event routing key names to match the catalog.

---

## 1. Inbound queue — replace `crisalid-ikg-user-actions` with `crisalid-ikg-actions-interactive`

### Current state

| Setting | Value |
|---|---|
| `amqp_user_actions_queue_name` | `"crisalid-ikg-user-actions"` |
| `amqp_user_actions_topic` | `"user_actions"` |
| Binding keys | `task.documents.document.*`, `task.people.person.*`, `task.people.documents.fetch` |

### Target state

| Setting | Value |
|---|---|
| `amqp_user_actions_interactive_queue_name` | `"crisalid-ikg-actions-interactive"` |
| `amqp_user_actions_interactive_topic` | `"user_actions_interactive"` |
| Binding keys | `task.documents.document.*.interactive`, `task.people.person.*.interactive`, `task.people.documents.fetch.interactive` |

The queue carries a DLQ as before:
- DLQ name: `dlq.crisalid-ikg-actions-interactive`
- Dead-letter exchange: `dlx.graph`
- Dead-letter routing key: `crisalid-ikg-actions-interactive`
(already reflected in `definitions.sample.json`)

### Changes required

**`app/settings/app_settings.py`**
- Remove `amqp_user_actions_queue_name`, `amqp_user_actions_topic`.
- Add `amqp_user_actions_interactive_queue_name` and `amqp_user_actions_interactive_topic`.
- Update binding key settings:
  - `amqp_graph_document_task_routing_key: str = "task.documents.document.*.interactive"`
  - `amqp_graph_person_documents_fetch_task_routing_key: str = "task.people.documents.fetch.interactive"`
  - `amqp_graph_person_attribute_update_task_routing_key: str = "task.people.person.*.interactive"`

**`app/amqp/amqp_interface.py`**
- Update `self.keys` to use the new topic key and the three new binding keys above.
- In `connect()`: replace the `_bind_queue` call for `user_actions` with a call using the new
  topic, queue name, and `with_dlq=True`.
- Update `_attach_message_processing_workers` call to use the new topic.

**`app/amqp/amqp_message_processor_factory.py`**
- Replace the `amqp_user_actions_topic` branch with `amqp_user_actions_interactive_topic`.

---

## 2. Outbound — 5th segment on all emitted messages

### Routing key convention

All messages emitted by crisalid-ikg (on both the `graph` and `publications` exchanges) gain a
5th segment:

```
<type>.<domain>.<entity>.<action>.<mode>
```

where `<mode>` is `"batch"` or `"interactive"`.

### Mode enum

`app/amqp/message_mode.py`:

```python
from enum import Enum

class MessageMode(str, Enum):
    BATCH = "batch"
    INTERACTIVE = "interactive"
```

### Mode rules

| Trigger origin | Mode | Exchange | Message |
|---|---|---|---|
| `PeopleService`, all `OrganizationUnit*Service` (directory ETL) | `batch` | `graph` | person / structure events |
| `DocumentService` (publication processing) | `batch` | `graph` | document events |
| `ChangeService.apply_change()` (non-MERGE) | `interactive` | `graph` | `document_updated` |
| MERGE path via `EquivalenceService` | `interactive` | `graph` | `document_updated/created` |
| `AMQPUserActionsMessageProcessor` — FETCH action | `interactive` | `publications` | `task.entity.references.retrieval` |
| `PeopleService` — person created/updated with identifier change | `batch` | `publications` | `task.entity.references.retrieval` |
| `AMQPHarvestingEventsMessageProcessor` | `batch` | `graph` | harvesting state/result events |

**Harvesting events are always `batch`.** There is no interactive path for harvesting events —
the interactive context is irrecoverably lost once the job enters svp-harvester's pipeline.
No interactive queue is declared for harvesting events.

### How mode flows through the system

Mode is a `mode` kwarg on `send_async` and on every signal handler that reaches an AMQP publisher.

**Graph exchange events** — add `mode` kwarg to signal sends:

```python
# batch (directory / harvester path)
await person_created.send_async(self, payload=uid, mode=MessageMode.BATCH)

# interactive (user action path)
await document_updated.send_async(self, document_uid=uid, mode=MessageMode.INTERACTIVE)
```

`AMQPInterface` dispatch methods extract `mode` from `**extra` (default `BATCH`) and forward it
to `_dispatch_*` helpers, which pass it to `publisher.publish(…, mode=mode)`.

**Publications exchange task** (`task.entity.references.retrieval`) — add `mode` kwarg to
`signal_publications_to_be_updated`:

```python
# in PeopleService — called from directory ETL
await publications_to_be_updated.send_async(self, payload={…}, mode=MessageMode.BATCH)

# in AMQPUserActionsMessageProcessor — called from a user FETCH action
await service.signal_publications_to_be_updated(person_uid, harvesters=harvesters,
                                                 mode=MessageMode.INTERACTIVE)
```

`PeopleService.signal_publications_to_be_updated` accepts an optional `mode` param (default
`BATCH`) and threads it through to `send_async`.

`AMQPInterface.fetch_publications` extracts `mode` from `**extra` and passes it to
`publisher.publish(…, mode=mode)`.

### `AMQPMessagePublisher.publish()` — append mode unconditionally

Mode is now appended to **all** outgoing messages, not only EVENT messages:

```python
async def publish(self, message_type, message_subtype, content,
                  mode: MessageMode = MessageMode.BATCH) -> None:
    payload, routing_key = await self._build_message(message_type, message_subtype, content)
    if routing_key is None or payload is None:
        return
    routing_key = f"{routing_key}.{mode.value}"   # applies to TASK and EVENT alike
    ...
```

Message factories continue to build base routing keys without a mode segment; the publisher
appends it.

---

## 3. Harvesting event routing key name fix

The current settings use incorrect 3rd-segment names. Update:

| Setting | Current value | New value |
|---|---|---|
| `amqp_graph_harvesting_state_event_routing_key` | `"event.harvestings.state.*"` | `"event.harvestings.harvesting_state_event.*"` |
| `amqp_graph_harvesting_result_event_routing_key` | `"event.harvestings.result.*"` | `"event.harvestings.harvesting_result_event.*"` |

After the publisher appends `.batch`, the full keys become:
- `event.harvestings.harvesting_state_event.running.batch`
- `event.harvestings.harvesting_result_event.created.batch`

These match the `event.harvestings.*.*.batch` wildcard binding on `sovisuplus-batch`. ✓

---

## 4. Settings summary

Remove:
- `amqp_user_actions_queue_name`
- `amqp_user_actions_topic`

Add:
- `amqp_user_actions_interactive_queue_name: str = "crisalid-ikg-actions-interactive"`
- `amqp_user_actions_interactive_topic: str = "user_actions_interactive"`

Update:
- `amqp_graph_document_task_routing_key`: `"task.documents.document.*.interactive"`
- `amqp_graph_person_documents_fetch_task_routing_key`: `"task.people.documents.fetch.interactive"`
- `amqp_graph_person_attribute_update_task_routing_key`: `"task.people.person.*.interactive"`
- `amqp_graph_harvesting_state_event_routing_key`: `"event.harvestings.harvesting_state_event.*"`
- `amqp_graph_harvesting_result_event_routing_key`: `"event.harvestings.harvesting_result_event.*"`

All other outbound routing key settings (people, structure, document events) remain as 4-segment
base keys; the publisher appends `.{mode}` at publish time.

---

## 5. What does NOT change

- All queues and exchanges other than `crisalid-ikg-user-actions` (directory, harvesting-events).
- Message payload schemas — this issue is routing-key / queue-topology only.
- `AMQPUserActionsMessageProcessor` processing logic — `actionType`/`targetType` values remain
  UPPERCASE Prisma enum values; only the routing key segment is lowercased on the sovisuplus side.
- `AbstractAMQPMessageFactory` and its subclasses — they keep building base routing keys without
  a mode segment.
- DLQ behavior — the new `crisalid-ikg-actions-interactive` queue still has a DLQ, same as before.

---

## 6. Testing

- `test_amqp_message_publisher.py`: verify EVENT routing keys append `.batch` by default;
  `task.entity.references.retrieval` also appends `.batch` by default; passing `INTERACTIVE`
  produces `.interactive`.
- `test_amqp_harvesting_events_message_processor.py`: expected routing keys use new 3rd-segment
  names and `.batch` suffix.
- `test_amqp_user_actions_message_processor.py` or integration test: verify that a FETCH action
  triggers `task.entity.references.retrieval.interactive`.