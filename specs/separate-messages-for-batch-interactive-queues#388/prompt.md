# Separate batch/interactive messages — 5th routing-key segment on the `graph` exchange

## Context

The CRISalid bus adopts a new convention for all messages on the `graph` exchange: every routing key gains a
**5th segment** `.interactive` or `.batch` that declares the traffic class of the message.

sovisuplus has already implemented its side (issue #827):
- It publishes task messages with the `.interactive` suffix and subscribes to two separate queues
  (`sovisuplus-interactive` / `sovisuplus-batch`) using wildcard bindings `event.*.*.*.interactive` and
  `event.*.*.*.batch`.
- `definitions.sample.json` in `crisalid-deployment` has already been updated accordingly.

This issue implements the **crisalid-ikg** side:

1. Rename/replace the inbound user-actions queue to `crisalid-ikg-actions-interactive` and update its binding
   keys to the new 5-segment format.
2. Add a **mode** (`batch` or `interactive`) to all outbound event messages published on the `graph` exchange.
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
- Remove old routing key settings: `amqp_graph_document_task_routing_key`,
  `amqp_graph_person_documents_fetch_task_routing_key`,
  `amqp_graph_person_attribute_update_task_routing_key`.
- Add `amqp_user_actions_interactive_queue_name` and `amqp_user_actions_interactive_topic`.
- Add updated routing keys:
  - `amqp_graph_document_task_routing_key: str = "task.documents.document.*.interactive"`
  - `amqp_graph_person_documents_fetch_task_routing_key: str = "task.people.documents.fetch.interactive"`
  - `amqp_graph_person_attribute_update_task_routing_key: str = "task.people.person.*.interactive"`

**`app/amqp/amqp_interface.py`**
- Update `self.keys` to use the new topic key and the three new binding keys above.
- In `connect()`: replace the `_bind_queue` call for `user_actions` with a call using the new topic,
  queue name, and `with_dlq=True`.
- Update `_attach_message_processing_workers` call to use the new topic.

**`app/amqp/amqp_message_processor_factory.py`**
- Replace the `amqp_user_actions_topic` branch with `amqp_user_actions_interactive_topic`.

---

## 2. Outbound — 5th segment on all `graph` exchange events — 5th segment on all `graph` exchange events

### Routing key convention

Every event message published to the `graph` exchange must now have a 5-segment routing key:

```
event.<domain>.<entity>.<action>.<mode>
```

where `<mode>` is `"batch"` or `"interactive"`.

### Mode enum

Add a `MessageMode` enum in the AMQP layer (e.g. in `app/amqp/amqp_message_publisher.py` or a
new `app/amqp/message_mode.py`):

```python
from enum import Enum

class MessageMode(str, Enum):
    BATCH = "batch"
    INTERACTIVE = "interactive"
```

### How mode flows through the system

The mode is determined by the **trigger origin** and must flow from the signal sender to the AMQP
publisher. The mechanism is a `mode` kwarg on every `send_async` call and on every signal handler.

**Mode rules:**

| Signal sender | Mode | Rationale |
|---|---|---|
| `PeopleService`, all `OrganizationUnit*Service` | `batch` | Always triggered by directory ETL |
| `DocumentService` (publication processing) | `batch` | Triggered by svp-harvester pipeline |
| `ChangeService.apply_change()` | `interactive` | Always triggered by a user action from sovisuplus |
| `AMQPHarvestingEventsMessageProcessor` | `batch` | Interactive context is lost through svp-harvester |

**Signal send call — add `mode` kwarg:**

```python
# before
await person_created.send_async(self, payload=uid)

# after
await person_created.send_async(self, payload=uid, mode=MessageMode.BATCH)
```

```python
# ChangeService — interactive
await document_updated.send_async(self, document_uid=change.target_uid, mode=MessageMode.INTERACTIVE)
```

**`AMQPInterface` dispatch methods — extract mode from kwargs:**

```python
async def dispatch_person_created(self, _, **extra) -> None:
    person_uid = extra["payload"]
    mode = extra.get("mode", MessageMode.BATCH)
    await self._dispatch_person_event(
        AMQPMessagePublisher.EventMessageSubtype.PERSON_CREATED, person_uid, mode
    )
```

All `_dispatch_*` helper methods must accept and forward a `mode` argument down to `publisher.publish()`.

**`AMQPMessagePublisher.publish()` — append mode to routing key:**

```python
async def publish(
    self,
    message_type: MessageType,
    message_subtype: MessageSubtype,
    content: dict,
    mode: MessageMode = MessageMode.BATCH,
) -> None:
    payload, routing_key = await self._build_message(message_type, message_subtype, content)
    if routing_key is None or payload is None:
        return
    routing_key = f"{routing_key}.{mode.value}"
    ...
```

Message factories (`AbstractAMQPMessageFactory` subclasses) continue to build **4-segment** base routing
keys — they do not change. The publisher appends the mode.

The `publish()` call for the `publications` exchange (publication retrieval task) does not receive a `mode`
parameter and does not append a suffix — the `task.entity.references.retrieval` key on the `publications`
exchange has no mode segment.

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

No changes are needed in the factory classes — they still replace `*` with the state/action value from the
content; the publisher appends the mode.

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

All other outbound routing key settings (people, structure, document events) remain as 4-segment base keys;
the publisher appends `.{mode}` at publish time.

---

## 5. What does NOT change

- All queues and exchanges other than `crisalid-ikg-user-actions` (directory, publications, harvesting-events).
- Message payload schemas — this issue is routing-key / queue-topology only.
- `AMQPUserActionsMessageProcessor` processing logic — the payload `actionType`/`targetType` values sent by sovisuplus remain UPPERCASE Prisma enum values (`"MERGE"`, `"FETCH"`, `"DOCUMENT"`, `"HARVESTING"`, …); only the routing key segment is lowercased on the sovisuplus side.
- `AbstractAMQPMessageFactory` and its subclasses — they keep building 4-segment routing keys.
- DLQ behavior — the new `crisalid-ikg-actions-interactive` queue still has a DLQ, same as before.

---

## 6. Testing

- Add / update unit tests for `AMQPMessagePublisher.publish()`: verify that the routing key returned by a
  factory is extended with `.batch` or `.interactive` depending on the `mode` argument.
- Existing `AMQPUserActionsMessageProcessor` tests remain valid — no payload format change.
- Add / update integration tests for `AMQPInterface` queue bindings: verify that the new binding keys are
  declared (not the old 4-segment ones).
