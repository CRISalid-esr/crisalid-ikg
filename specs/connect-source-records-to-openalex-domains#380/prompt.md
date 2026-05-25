# Connect Source Records to OpenAlex Topics — Issue #380

## Context

The harvester now sends a `domains` field on each reference event (see svp-harvester#897). For
OpenAlex records this field contains a list of topics with their relevance score. This feature
wires those topic references into the knowledge graph by linking each `SourceRecord` to the
matching `Topic` nodes via a `HAS_TOPIC` relationship carrying the score.

Topic nodes already exist in Neo4j: they are bulk-loaded at startup by `Neo4jDomainSetup` from an
OpenAlex snapshot. This feature never creates or modifies `Topic` nodes — it only creates and
maintains the `HAS_TOPIC` relationship.

---

## AMQP payload (incoming)

The harvester emits `domains` under `reference_event.reference`. For OpenAlex records:

```json
"domains": [
  {
    "source_id": "T10153",
    "uri":        "https://openalex.org/T10153",
    "label":      "Education, sociology, and vocational training",
    "score":      0.9588
  },
  {
    "source_id": "T11475",
    "uri":        "https://openalex.org/T11475",
    "label":      "French Urban and Social Studies",
    "score":      0.9486
  }
]
```

Other harvesters send an empty `domains` array. `source_id` and `label` are informational only
from the IKG's perspective; only `uri` and `score` are used.

---

## Data model

### New dataclass — `SourceRecordDomain`

Create `app/models/source_record_domain.py`:

```python
from dataclasses import dataclass

@dataclass
class SourceRecordDomain:
    uri: str
    score: float | None = None
```

A plain dataclass is sufficient — there is no validation logic, no serialization, and no need for
Pydantic's overhead. Pydantic v2 accepts standard dataclasses as field types and will coerce dict
inputs into them transparently. The type is intentionally generic (not `Topic`) so a future
non-OpenAlex taxonomy can slot in without a model change. `source_id` and `label` from the wire
format are discarded at deserialization time.

### `SourceRecord` — new field

```python
domains: List[SourceRecordDomain] = []
```

Add a field validator that accepts the full wire format `{source_id, uri, label, score}` and
strips it down to `{uri, score}`:

```python
@field_validator("domains", mode="before")
@classmethod
def _coerce_domains(cls, v):
    return [{"uri": d["uri"], "score": d.get("score")} if isinstance(d, dict) else d for d in (v or [])]
```

### Neo4j graph

New relationship on `SourceRecord` nodes:

```
(s:SourceRecord)-[:HAS_TOPIC {score: <float>}]->(t:Topic:Concept)
```

- `Topic` nodes are matched by `uri` property (the full OpenAlex URI).
- The `score` property lives on the relationship, not the node.
- `Field`, `SubField`, and `Domain` ancestry is already encoded via `BROADER` edges; it does not
  need to be recorded on the source record.

---

## New Cypher query

### `sync_source_record_topics.cypher`

Replaces all `HAS_TOPIC` edges on a source record in one atomic operation:

```cypher
MATCH (s:SourceRecord {uid: $source_record_uid})

// Remove all existing topic links for this source record
OPTIONAL MATCH (s)-[r:HAS_TOPIC]->()
DELETE r

// Re-create from the supplied list
WITH s
UNWIND $topics AS t
MATCH (topic:Topic {uri: t.uri})
MERGE (s)-[rel:HAS_TOPIC]->(topic)
SET rel.score = t.score  // null when not provided
```

Parameters: `source_record_uid` (string), `topics` (list of `{uri, score}` maps).

If a URI is absent from the graph, the inner `MATCH` simply returns no rows for that entry
(no error, no partial write). Missing topics are detected and reported at the service layer before
this query is called.

---

## Service layer — `SourceRecordService`

Add a private method `_handle_source_record_domains`:

```python
async def _handle_source_record_domains(self, source_record: SourceRecord) -> None:
    concept_dao = ConceptDAO()
    valid_topics = []
    for domain in source_record.domains:
        topic = await concept_dao.find_by_uri(domain.uri)
        if topic is None:
            logger.error(
                f"Topic with URI {domain.uri} not found in graph "
                f"(source record {source_record.uid}) — skipping"
            )
            continue
        valid_topics.append(domain)
    source_record_dao: SourceRecordDAO = self._get_dao_factory().get_dao(SourceRecord)
    await source_record_dao.sync_topics(source_record.uid, valid_topics)
```

Call `_handle_source_record_domains` in **both** `create_source_record` and
`update_source_record`, after the main DAO write:

```python
await self._handle_source_record_domains(source_record)
```

---

## DAO layer — `SourceRecordDAO`

Add a public method `sync_topics`:

```python
@handle_database_errors
async def sync_topics(
    self, source_record_uid: str, domains: List[SourceRecordDomain]
) -> None:
    async with Neo4jConnexion().get_driver() as driver:
        async with driver.session() as session:
            await session.run(
                load_query("sync_source_record_topics"),
                source_record_uid=source_record_uid,
                topics=[{"uri": d.uri, "score": d.score} for d in domains],
            )
```

The method runs outside an explicit transaction (consistent with similar single-query operations
in this DAO). It is called even when `domains` is empty — the Cypher will then delete any
previously recorded topic links, which is the correct update semantics.

---

## Update semantics

On every create or update of a source record:

1. Resolve each `domain.uri` against existing `Topic` nodes (Python loop, via `ConceptDAO`).
2. Log an error for each URI that does not exist; skip it.
3. Call `sync_topics` with the validated list — this atomically deletes old `HAS_TOPIC` edges and
   creates new ones from the list.

Topic nodes are **never** deleted or modified. If the new payload contains fewer topics than the
previous version, the removed edges simply disappear; the Topic nodes remain.

---

## Out of scope

- Creating Topic nodes on the fly from incoming AMQP data.
- Recording `HAS_TOPIC` relationships on `Document` nodes (links to `SourceRecord` suffice).
- Linking source records to `Field`, `SubField`, or `Domain` nodes (inferable from the hierarchy).
- Hydrating `domains` when reading a `SourceRecord` back from the graph (`_hydrate`): the
  relationship is write-only for now.
- Any changes to the Elasticsearch source record index.

---

## Files to create / modify

| File | Action |
|---|---|
| `app/models/source_record_domain.py` | **Create** — `SourceRecordDomain` model |
| `app/models/source_records.py` | **Modify** — add `domains` field + validator |
| `app/graph/neo4j/queries/sync_source_record_topics.cypher` | **Create** |
| `app/graph/neo4j/source_record_dao.py` | **Modify** — add `sync_topics` method |
| `app/services/source_records/source_record_service.py` | **Modify** — add `_handle_source_record_domains`, call it in create + update |

---

## Tests

- Unit test for the `_coerce_domains` field validator: full wire-format dict is accepted and
  stripped to `{uri, score}`.
- Integration test for `create_source_record` with domains: verify `HAS_TOPIC` edges exist in
  Neo4j with the correct `score`.
- Integration test for `update_source_record` with a changed domain list: old edges are removed,
  new edges are created.
- Integration test for a topic URI that does not exist in the graph: the source record is still
  created/updated (no exception), an error is logged, and no `HAS_TOPIC` edge is created for the
  unknown URI.
- Integration test for an empty `domains` list on update: any existing `HAS_TOPIC` edges are
  removed.
