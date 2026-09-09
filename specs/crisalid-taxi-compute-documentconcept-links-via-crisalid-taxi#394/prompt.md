# Compute Document–Topic Links via Crisalid-taxi — Issue #394

## Context

Issue #380 linked each `SourceRecord` to OpenAlex `Topic` nodes (`HAS_TOPIC` with a `score`) from
the topics the harvester receives from OpenAlex. It explicitly left "recording `HAS_TOPIC`
relationships on `Document` nodes" out of scope. This feature closes that gap and adds a second,
independent source of topics: **Crisalid-taxi**, an external semantic classifier that embeds a free
text and returns the closest OpenAlex concepts above a cosine-similarity threshold.

At the end of this feature, every `Document` can carry two kinds of `HAS_TOPIC` edges towards
`Concept:Topic` nodes, distinguished by a `source` property:

| `source`   | Origin                                                                 |
|------------|------------------------------------------------------------------------|
| `openalex` | Propagated from the `HAS_TOPIC` edges of the document's source records |
| `crisalid` | Computed by Crisalid-taxi from the document's title, abstract and subjects |

Topic nodes already exist in Neo4j (bulk-loaded at startup by `Neo4jDomainSetup`, see
`upsert_openalex_topic.cypher`: `uid == uri == "https://openalex.org/T11347"`). This feature never
creates or modifies `Topic` nodes — it only creates and maintains relationships.

The Crisalid-taxi call runs **during document computation**, in `DocumentService`, so that the
`document_created` / `document_updated` AMQP messages already contain the topics when they are
published. It runs **in parallel** with the Unpaywall call, never adds a failure path to document
computation, and is skipped when the input text has not changed since the last successful call.

---

## Crisalid-taxi API

Only `POST /api/v1/match/` is used. `GET /liveness` and `GET /readiness` exist but are not called
by IKG.

**Request** — a list of inputs, each with a caller-chosen `id`:

```json
{
  "inputs": [
    { "id": "doc-uid-1", "text": "Machine learning algorithms for quantum computing physics simulations" },
    { "id": "doc-uid-2", "text": "Taxonomy of soccer training methods" }
  ],
  "similarity_threshold": 0.53
}
```

**Response (200 OK)**:

```json
{
  "generated_at": "20260615T113123Z",
  "model": "bge-m3",
  "query_count": 2,
  "total_matches": 2,
  "similarity_threshold": 0.53,
  "results": [
    {
      "id": "doc-uid-1",
      "matches": [
        { "concept_uid": "https://openalex.org/T11347", "rel_type": "HAS_TOPIC",    "value": 0.765432 },
        { "concept_uid": "https://openalex.org/subfields/111", "rel_type": "HAS_SUBFIELD", "value": 0.612345 }
      ]
    },
    { "id": "doc-uid-2", "matches": [] }
  ]
}
```

**Error (500)**: `{ "detail": "internal error description" }`.

IKG uses `model`, and for each result `id` → `matches[].concept_uid / rel_type / value`.
Only `rel_type == "HAS_TOPIC"` matches are kept; `HAS_SUBFIELD`, `HAS_FIELD`, `HAS_DOMAIN` and any
other type are ignored.

---

## Settings

Add to `AppSettings` (`app/settings/app_settings.py`), right after the `embedding_*` block, using
the same style (plain annotated attributes, no `Field`, env var = upper-cased name; JSON syntax
for the list, like `HARVESTERS`):

```python
taxi_enabled: bool = False
taxi_api_url: str = ""
taxi_timeout_seconds: int = 30
taxi_languages: List[str] = ["en", "fr"]
taxi_min_input_length: int = 25
taxi_max_topics: int = 30
taxi_similarity_threshold: float = 0.53
taxi_batch_size: int = 50
taxi_max_consecutive_failures: int = 5
taxi_circuit_open_seconds: int = 300
```

Document them in `.env.example` (after the `EMBEDDING_*` block) and in `docker-compose.yml.dist`:

```env
TAXI_ENABLED=false
TAXI_API_URL="http://localhost:8000"
TAXI_TIMEOUT_SECONDS=30
# JSON list, priority order: the first language with a title or abstract is used
TAXI_LANGUAGES=["en", "fr"]
# minimum length of title + abstract (characters) below which Taxi is not called
TAXI_MIN_INPUT_LENGTH=25
# maximum number of source="crisalid" HAS_TOPIC edges per document
TAXI_MAX_TOPICS=30
# minimum cosine similarity; sent to Taxi and re-applied client-side
TAXI_SIMILARITY_THRESHOLD=0.53
# number of documents per Taxi request in the CLI recompute command
TAXI_BATCH_SIZE=50
# circuit breaker: after N consecutive failures, stop calling Taxi for M seconds
TAXI_MAX_CONSECUTIVE_FAILURES=5
TAXI_CIRCUIT_OPEN_SECONDS=300
```

Semantics:

- `taxi_enabled=False` (default) → no Taxi call, no read of the topics state, no new CLI behaviour.
  The `openalex` edge propagation (below) is **not** gated by this flag: it has no external
  dependency.
- `taxi_timeout_seconds` is a dedicated `aiohttp.ClientTimeout(total=...)` for the Taxi session,
  like `embedding_timeout_seconds`. The shared `AioHttpClientManager` session and its 7 s
  `http_client_timeout_total` are **not** used for Taxi.
- `taxi_similarity_threshold` is always sent as `similarity_threshold` in the request **and**
  re-applied client-side on `value` (defensive: the server default may differ).
- Add a README section "Document topics via Crisalid-taxi (optional)" modelled on the existing
  "Embeddings (optional)" section: opt-in flag, settings block, how topics are computed (during
  document computation vs CLI), the hash-skip rule, the circuit breaker, the two edge sources.

---

## Data model

### Graph

```
(Document)-[:HAS_TOPIC {source: 'openalex', score}]->(Concept:Topic)
(Document)-[:HAS_TOPIC {source: 'crisalid', score, model, computed_at}]->(Concept:Topic)
```

Edge properties:

| Property      | `openalex`                                            | `crisalid`                              |
|---------------|-------------------------------------------------------|-----------------------------------------|
| `source`      | `"openalex"`                                          | `"crisalid"`                            |
| `score`       | max `score` over the document's source-record edges   | Taxi match `value`                      |
| `model`       | —                                                     | Taxi response `model` (e.g. `bge-m3`)   |
| `computed_at` | —                                                     | `datetime()` at write time              |

`score` is used for both sources (same name as on `(SourceRecord)-[:HAS_TOPIC]`), so consumers
read a single property whatever the origin.

New properties on the `Document` node, written **only** by a successful Taxi round-trip, together
with the edges (see the single-statement Cypher below):

| Property             | Meaning                                                            |
|----------------------|--------------------------------------------------------------------|
| `topics_input_hash`  | `sha256` hex digest of the exact `text` sent to Taxi               |
| `topics_model`       | Taxi `model` of the last successful call                           |
| `topics_computed_at` | `datetime()` of the last successful call                           |

`topics_input_hash` is the skip key: when the rebuilt input text hashes to the stored value, Taxi
is not called (same idea as `embedding_hash` in `EmbeddingService`). Because the hash is only
written on success, a failed call leaves the previous hash in place and the next computation
retries.

No new constraint or index is required (`Document.uid` and `Concept.uid` already have uniqueness
constraints).

### Pydantic — `DocumentTopic` and `Document.topics`

In `app/models/document.py`:

```python
class DocumentTopic(BaseModel):
    """A Document -> Topic link, whatever its origin."""
    uid: str
    uri: Optional[str] = None
    display_name: Optional[str] = None
    source: str                      # "openalex" | "crisalid"
    score: Optional[float] = None
    model: Optional[str] = None      # crisalid only
```

Add `topics: List[DocumentTopic] = []` to `Document`. The field is **read-only from the graph**:
it is filled by `DocumentDAO._hydrate`, never by the merge strategies, and never used as an input
to a write (the write path uses `TopicsResult`, below). It is exposed in the AMQP document payload
(see "AMQP payload").

### Service-level result objects (`app/services/documents/topics_computation_service.py`)

```python
@dataclass
class TopicsResult:
    document_uid: str
    input_hash: str
    model: str
    topics: list[tuple[str, float]]   # (concept uid, score), sorted by score desc, len <= taxi_max_topics
```

Plain dataclasses, no validation logic — same reasoning as `SourceRecordDomain` in #380.

---

## Input text builder

New pure module `app/services/documents/topics_input_builder.py` (no I/O, fully unit-testable):

```python
UNDETERMINED = {"und", "ul"}   # Literal default is "ul", Cypher stores "und"

@dataclass
class TopicsInput:
    text: str
    language: str
    input_hash: str

def select_language(titles: list[Literal], abstracts: list[TextLiteral],
                    languages: list[str]) -> str | None:
    """First language of `languages` (priority order) that has at least one title or
    abstract; else 'und' if any title/abstract has an undetermined language; else None."""

def build_topics_input(titles, abstracts, subjects: list[Concept],
                       languages: list[str], min_input_length: int) -> TopicsInput | None:
```

Rules for `build_topics_input`:

1. `language = select_language(...)`. `None` → return `None` (debug log: no usable language).
2. Take, in this order, the titles then the abstracts whose `language` is `language`
   (when `language == "und"`, match on `UNDETERMINED`). Strip and collapse whitespace.
3. `core = ". ".join(title_values + abstract_values)`.
   If `len(core) < min_input_length` → return `None` (debug log: input too short). **Subjects do
   not count toward the minimum**: a document with only subjects is not sent.
4. Subjects: the `pref_labels` of `subjects` in the same `language` (same `und` rule), stripped,
   deduplicated case-insensitively, order preserved. **`alt_labels` are never used.**
5. `text = ". ".join([core] + pref_label_values)`.
6. `input_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()`.

No translation, no cross-language merging, no per-language multiple requests.

---

## Crisalid-taxi client

New module `app/services/documents/crisalid_taxi_client.py`:

```python
@dataclass
class TaxiMatch:
    concept_uid: str
    rel_type: str
    value: float

@dataclass
class TaxiMatchResponse:
    model: str
    results: dict[str, list[TaxiMatch]]   # keyed by input id

class CrisalidTaxiClient:
    _consecutive_failures: ClassVar[int] = 0
    _open_until: ClassVar[float | None] = None      # time.monotonic() deadline

    def __init__(self):
        settings = get_app_settings()
        if not settings.taxi_api_url:
            raise ValueError("TAXI_API_URL must be set when TAXI_ENABLED is true")
        self._url = settings.taxi_api_url.rstrip("/") + "/api/v1/match/"
        self._timeout = aiohttp.ClientTimeout(total=settings.taxi_timeout_seconds)
        self.settings = settings

    async def match(self, inputs: list[dict]) -> TaxiMatchResponse | None: ...

    @classmethod
    def is_open(cls) -> bool: ...
    @classmethod
    def reset(cls) -> None: ...
```

`match()` behaviour:

- If the circuit is open (`_open_until` set and not yet elapsed) → return `None` immediately, no
  HTTP, debug log. When the deadline has elapsed, the circuit is *half-open*: the call is
  attempted; success closes it (`reset()`), failure re-opens it for another
  `taxi_circuit_open_seconds`.
- Payload: `{"inputs": inputs, "similarity_threshold": settings.taxi_similarity_threshold}`.
- HTTP: `async with aiohttp.ClientSession(timeout=self._timeout) as session: async with
  session.post(self._url, json=payload) as response:` — a dedicated session per call, exactly
  as `OpenAICompatibleProvider.embed_texts`. In `APP_ENV=TEST`, raise `RuntimeError` unless
  `aiohttp.ClientSession` is mocked (same guard idea as `ApiService._fetch_json`).
- Any failure — non-200 status, `aiohttp.ClientError`, `asyncio.TimeoutError`, JSON decode
  error, missing `results`/`model` keys — is logged with `logger.error` (status + `detail` when
  present) and returns `None`. **The client never raises into callers.**
- On failure: `_consecutive_failures += 1`; when it reaches
  `taxi_max_consecutive_failures`, set `_open_until = monotonic() + taxi_circuit_open_seconds`
  and log **one** warning: `"Crisalid-taxi circuit opened after N consecutive failures; calls
  suspended for M s"`. On success: `_consecutive_failures = 0`, `_open_until = None`.
- The breaker state is class-level, i.e. **per process**. Each AMQP worker process and each CLI
  run has its own; there is no shared/persistent state (out of scope).

---

## `TopicsComputationService`

New `app/services/documents/topics_computation_service.py`:

```python
class TopicsComputationService:
    def __init__(self):
        self.settings = get_app_settings()

    async def compute_topics_for_document(
            self, document_uid: str, document: Document,
            previous_hash: str | None, force: bool = False) -> TopicsResult | None:
```

Steps (each early return is a *skip*: nothing is written, existing `crisalid` edges are kept):

1. `taxi_enabled` false → `None`.
2. `topics_input = build_topics_input(document.titles, document.abstracts, document.subjects,
   self.settings.taxi_languages, self.settings.taxi_min_input_length)`; `None` → skip.
3. `not force and topics_input.input_hash == previous_hash` → skip (debug log
   `"topics input unchanged for {uid}"`). This is the request-reduction mechanism: no call when
   title, abstract and subjects are unchanged.
4. `response = await CrisalidTaxiClient().match([{"id": document_uid, "text": topics_input.text}])`;
   `None` → skip (error already logged by the client; **no wipe**).
5. `topics = self._filter(response.results.get(document_uid, []))`:
   keep `rel_type == "HAS_TOPIC"` and `value >= taxi_similarity_threshold`; sort by `value`
   desc; keep the first `taxi_max_topics`.
6. Return `TopicsResult(document_uid, topics_input.input_hash, response.model, topics)`.
   An **empty** `topics` list is a valid result: the document has no topic above the threshold,
   stale `crisalid` edges must be wiped and the hash recorded.

Use `document_uid` (the method parameter) as the Taxi input id — in
`_compute_document_from_source_records` the merged `document.uid` is only assigned after the
computation step.

Batch variant for the CLI:

```python
    async def compute_topics_batch(
            self, rows: list[DocumentTopicsRow], force: bool = False
    ) -> tuple[list[TopicsResult], TopicsBatchStats]:
```

`DocumentTopicsRow` is the DAO read model (`uid`, `titles`, `abstracts`, `subject_pref_labels`,
`topics_input_hash`). For each row apply steps 2–3; the rows that survive form **one** Taxi
request (`inputs` of up to `taxi_batch_size` items, ids = document uids). If the client returns
`None`, the whole batch is skipped (stats `failed += len(batch)`). Otherwise apply step 5 per
result and build one `TopicsResult` per document. `TopicsBatchStats` counts
`skipped_no_input / skipped_unchanged / failed / computed`.

Missing concept nodes: the write Cypher matches `Concept:Topic` by `uid` and silently drops
unknown uids. The DAO returns the list of uids actually linked; the service logs
`logger.warning("Topic {uid} returned by Crisalid-taxi not found in graph (document {doc}) —
skipped")` for each requested-but-not-linked uid.

Wrap the whole `compute_topics_for_document` body in `try/except Exception` → `logger.exception`,
return `None`. Document computation must never fail because of topics.

---

## Service layer — `DocumentService`

### Parallelism with Unpaywall

In `_compute_document_from_source_records` (`app/services/documents/document_service.py`),
replace

```python
document = await OAColorsComputationService(document, sources_records).compute_oa_colors()
```

with

```python
dao: DocumentDAO = cast(DocumentDAO, self._get_dao_factory().get_dao(Document))
previous_hash = (await dao.get_topics_state(document_uid)
                 if self.settings.taxi_enabled else None)
document, topics_result = await asyncio.gather(
    OAColorsComputationService(document, sources_records).compute_oa_colors(),
    TopicsComputationService().compute_topics_for_document(
        document_uid, document, previous_hash),
)
```

The two coroutines touch disjoint state: `compute_oa_colors` mutates
`document.open_access_status` and returns the document; the topics service only reads
`titles` / `abstracts` / `subjects` and returns a `TopicsResult`. Total latency becomes
`max(unpaywall, taxi)` instead of the sum.

Then, **after** `await dao.create_or_update_document(document)` and **before**
`ChangeService().apply_changes_to_node(...)`:

```python
if topics_result is not None:
    await dao.sync_crisalid_topics(topics_result)
```

Ordering guarantees:

- `create_or_update_document` runs first so the `Document` node exists on creation and its
  `openalex` edges are refreshed in the same transaction (below).
- `sync_crisalid_topics` runs before the method returns, hence before the callers emit
  `document_created` / `document_updated`. The AMQP message factory re-reads the document
  (`DocumentService.get_document`) and therefore sees both kinds of topics.
- The `to_be_deleted` early return (no source records) happens before any write, as today;
  a document being deleted gets no Taxi call result written.

### Reading

`DocumentService.get_document` is unchanged; `topics` arrive through `_hydrate`.

---

## DAO layer — `DocumentDAO` and Cypher

All new queries live in `app/graph/neo4j/queries/`; all new DAO methods are `async`, decorated
with `@handle_database_errors`, and use `session.run(load_query(...))` like
`SourceRecordDAO.sync_topics`.

### `sync_document_openalex_topics.cypher` — propagation from source records

Run as the **fourth statement** of `DocumentDAO._create_or_update_document_transaction`, after
`update_document_publication_channels`, in the same write transaction:

```cypher
MATCH (doc:Document {uid: $document_uid})
OPTIONAL MATCH (doc)-[old:HAS_TOPIC {source: 'openalex'}]->()
DELETE old
WITH DISTINCT doc
OPTIONAL MATCH (doc)-[:RECORDED_BY]->(:SourceRecord)-[r:HAS_TOPIC]->(topic:Concept:Topic)
WITH doc, topic, max(r.score) AS score
WHERE topic IS NOT NULL
MERGE (doc)-[rel:HAS_TOPIC {source: 'openalex'}]->(topic)
SET rel.score = score
```

Parameters: `document_uid`. When several source records share a topic the highest score wins.
Because `RECORDED_BY` edges are synchronised earlier in the same transaction, the propagation
always reflects the current set of source records. Not gated by `taxi_enabled`.

### `sync_document_crisalid_topics.cypher` — single wipe-and-write statement

```cypher
MATCH (doc:Document {uid: $document_uid})
OPTIONAL MATCH (doc)-[old:HAS_TOPIC {source: 'crisalid'}]->()
DELETE old
WITH DISTINCT doc
SET doc.topics_input_hash = $input_hash,
    doc.topics_model = $model,
    doc.topics_computed_at = datetime()
WITH doc
UNWIND CASE WHEN size($topics) = 0 THEN [null] ELSE $topics END AS t
OPTIONAL MATCH (topic:Concept:Topic {uid: t.uid})
FOREACH (_ IN CASE WHEN topic IS NULL THEN [] ELSE [1] END |
  MERGE (doc)-[rel:HAS_TOPIC {source: 'crisalid'}]->(topic)
  SET rel.score = t.score, rel.model = $model, rel.computed_at = datetime()
)
RETURN collect(DISTINCT topic.uid) AS linked_uids
```

Parameters: `document_uid`, `input_hash`, `model`, `topics = [{uid, score}, ...]`.

Properties of this statement:

- Wipe and write are **one statement**, so the graph never exposes a "no crisalid edges" state
  between the two, and a failure leaves the previous edges untouched.
- Only `source = 'crisalid'` edges are removed; `openalex` edges (and `HAS_SUBJECT`) are never
  touched.
- The `CASE ... [null]` guard keeps the row alive when `$topics` is empty so the wipe and the
  `SET` still happen (empty result = document has no topic above threshold).
- Unknown concept uids yield `topic = null`, create nothing, and are absent from `linked_uids`;
  the service turns the difference into warnings.
- Called **only** with a `TopicsResult`, i.e. only after a usable Taxi response. Never called on
  HTTP failure, timeout, open circuit, short input or unchanged hash.

### `sync_documents_crisalid_topics_batch.cypher` — CLI batch write

Same body wrapped in `UNWIND $rows AS row` (`row = {document_uid, input_hash, model, topics}`),
returning `row.document_uid AS document_uid, collect(DISTINCT topic.uid) AS linked_uids`. One
write transaction per batch.

### `get_document_topics_state.cypher`

```cypher
MATCH (doc:Document {uid: $document_uid})
RETURN doc.topics_input_hash AS input_hash, doc.topics_model AS model
```

`DocumentDAO.get_topics_state(uid) -> str | None` returns `input_hash` (`None` when the
document does not exist yet or was never computed).

### `get_documents_for_topics_computation.cypher` — CLI paging

```cypher
MATCH (doc:Document)
WHERE coalesce(doc.to_be_deleted, false) = false
  AND ($missing_only = false
       OR (doc.topics_input_hash IS NULL
           AND NOT (doc)-[:HAS_TOPIC {source: 'crisalid'}]->()))
WITH doc ORDER BY doc.uid SKIP $skip LIMIT $limit
OPTIONAL MATCH (doc)-[:HAS_TITLE]->(t:Literal {type: 'document_title'})
OPTIONAL MATCH (doc)-[:HAS_ABSTRACT]->(a:TextLiteral {type: 'document_abstract'})
OPTIONAL MATCH (doc)-[:HAS_SUBJECT]->(:Concept)-[:HAS_PREF_LABEL]->(pl:Literal)
RETURN doc.uid AS uid,
       doc.topics_input_hash AS topics_input_hash,
       collect(DISTINCT {value: t.value, language: t.language}) AS titles,
       collect(DISTINCT {value: a.value, language: a.language}) AS abstracts,
       collect(DISTINCT {value: pl.value, language: pl.language}) AS subject_pref_labels
```

Paging is by `uid` order over a stable predicate. With `--missing-only`, the predicate shrinks as
documents get their hash; the CLI therefore **does not advance `skip`** in that mode (always
re-reads page 0 until empty), and advances `skip` normally otherwise. This avoids the
skip/limit drift present in `EmbeddingService._process_pending`.

`DocumentDAO.get_documents_for_topics_computation(skip, limit, missing_only) ->
list[DocumentTopicsRow]`.

### `count_documents_by_topics_state.cypher`

```cypher
MATCH (doc:Document)
RETURN count(doc) AS total,
       count(doc.topics_input_hash) AS computed,
       count { (doc)-[:HAS_TOPIC {source: 'crisalid'}]->() } AS crisalid_edges,
       count { (doc)-[:HAS_TOPIC {source: 'openalex'}]->() } AS openalex_edges
```

Used by the CLI for before/after reporting (`DocumentDAO.count_topics_state()`).

### Reading — `get_document_by_uid.cypher` and `_hydrate`

Add to `get_document_by_uid.cypher`:

```cypher
OPTIONAL MATCH (document)-[ht:HAS_TOPIC]->(topic:Concept:Topic)
...
collect(DISTINCT CASE WHEN topic IS NOT NULL THEN {
  uid: topic.uid, uri: topic.uri, display_name: topic.display_name,
  source: ht.source, score: ht.score, model: ht.model
} END) AS topics
```

(carry `ht`/`topic` through the existing `WITH` chain, or collect them in a dedicated `WITH`
right after the `OPTIONAL MATCH` to avoid row multiplication with contributions). In
`DocumentDAO._hydrate`: `document.topics = [DocumentTopic(**t) for t in record["topics"] if t]`.

`get_document_by_source_record_uid.cypher` is left unchanged (topics are not needed there).

---

## AMQP payload

In `AMQPDocumentEventMessageFactory._build_document_message_payload`, add:

```python
"topics": [topic.model_dump() for topic in document.topics],
```

Each entry: `{uid, uri, display_name, source, score, model}`. Consumers filter on `source` when
they only want one origin. Since `sync_crisalid_topics` completes before the signals are
emitted, the message published for a created/updated document already carries the fresh
`crisalid` topics — this is why the Taxi call is kept synchronous within document computation
rather than deferred.

---

## CLI — `documents recompute-topics`

In `app/commands/documents.py`, following the `literals compute-embeddings` pattern (options on
the outer sync function, work in a nested `@with_app_lifecycle` coroutine, lazy imports with
`# pylint: disable=import-outside-toplevel`, feature-flag guard → `typer.Exit(code=1)`).

### `documents recompute-topics <uid>`

```bash
APP_ENV=DEV python -m app.cli documents recompute-topics local-D123
```

Single document. Reads the document (`DocumentService.get_document`), calls
`compute_topics_for_document(uid, document, previous_hash=None, force=True)` — the hash is
**ignored** for an explicit single-document request — then `sync_crisalid_topics`. Echoes the
linked topics (`uid`, `score`) or the skip reason (too short, no language, Taxi failure).
Emits `document_updated` (batch mode) unless `--no-dispatch`.

### `documents recompute-topics-all`

```bash
APP_ENV=DEV python -m app.cli documents recompute-topics-all \
    [--missing-only] [--force] [--batch-size 50] [--no-dispatch]
```

| Option           | Default           | Effect                                                                 |
|------------------|-------------------|------------------------------------------------------------------------|
| `--missing-only` | off               | Only documents with no `crisalid` edge **and** no `topics_input_hash`  |
| `--force`        | off               | Ignore `topics_input_hash` (use after a Taxi model change)             |
| `--batch-size`   | `TAXI_BATCH_SIZE` | Documents per Taxi request and per write transaction                    |
| `--no-dispatch`  | off               | Do not emit `document_updated` events                                   |

Algorithm:

1. Guard `taxi_enabled`; echo `count_topics_state()`.
2. Page through `get_documents_for_topics_computation(skip, batch_size, missing_only)` (see the
   paging note above for `--missing-only`).
3. For each page: `results, stats = compute_topics_batch(rows, force=force)`; then
   `linked = await dao.sync_crisalid_topics_batch(results)`.
4. For each written document whose edge set changed (compare the set of `(uid, score)` before —
   returned by the batch write as `previous_uids` — with the new one), emit
   `document_updated.send_async(None, document_uid=uid, mode=MessageMode.BATCH)` unless
   `--no-dispatch`.
5. If `CrisalidTaxiClient.is_open()` becomes true, echo
   `"Crisalid-taxi circuit open — stopping; rerun later or raise TAXI_MAX_CONSECUTIVE_FAILURES"`
   and exit with code 2 (the documents already written are kept).
6. Echo cumulative stats per page (`computed / skipped_unchanged / skipped_no_input / failed`)
   and the final `count_topics_state()`.

Without `--force`, `recompute-topics-all` is cheap to rerun: documents whose text has not changed
never reach Taxi.

Batch writes should also return the previous `crisalid` uids so step 4 can decide whether an
event is needed; extend `sync_documents_crisalid_topics_batch.cypher` with
`collect(DISTINCT old_topic.uid) AS previous_uids` captured before the `DELETE`.

---

## Startup and feature flag

- No new signal and no new startup wiring: the Taxi call is invoked directly by
  `DocumentService`, guarded by `taxi_enabled`.
- `CrisalidTaxiClient` is instantiated lazily per call (cheap: it only builds a URL and a
  timeout); a `ValueError` for a missing `TAXI_API_URL` is caught by the service's `try/except`
  and logged, so a misconfigured deployment degrades to "no crisalid topics" rather than
  breaking document computation.
- Update the `CLAUDE.md` graph-model section: `Document -[:HAS_TOPIC {source, score, model}]->
  Concept:Topic` with the two sources, and the `topics_*` node properties.

---

## Update semantics (summary)

On each document computation:

1. `openalex` edges are always rebuilt from the current source records (same transaction as the
   document write).
2. `crisalid` edges are rebuilt **only** when all of: `taxi_enabled`, usable input (language
   match, `len(title+abstract) >= taxi_min_input_length`), input hash changed, circuit closed,
   Taxi answered 200 with a well-formed body. Then the old `crisalid` edges are wiped and the new
   ones written in one statement, together with `topics_input_hash / topics_model /
   topics_computed_at`.
3. In every other case the previous `crisalid` edges and hash are left untouched.

---

## Out of scope

- Non-`HAS_TOPIC` match types (`HAS_SUBFIELD`, `HAS_FIELD`, `HAS_DOMAIN`): ignored, not stored.
- Translation, multi-language queries, cross-language merging.
- Retry / backoff beyond the circuit breaker; persistent or cross-process breaker state.
- Hydrating `HAS_TOPIC` on `SourceRecord` (still write-only, as in #380).
- Exposing topics through the HTTP API (`/api/v0/...`).
- Deriving topics for documents that have neither title nor abstract in a configured language.

---

## Files to create / modify

| File | Action |
|------|--------|
| `app/settings/app_settings.py` | **Modify** — `taxi_*` settings |
| `.env.example`, `docker-compose.yml.dist`, `README.md`, `CLAUDE.md` | **Modify** — document settings, graph model |
| `app/models/document.py` | **Modify** — `DocumentTopic`, `Document.topics` |
| `app/services/documents/topics_input_builder.py` | **Create** — language selection, text + hash |
| `app/services/documents/crisalid_taxi_client.py` | **Create** — HTTP client, timeout, circuit breaker |
| `app/services/documents/topics_computation_service.py` | **Create** — single + batch computation, filtering |
| `app/services/documents/document_service.py` | **Modify** — `gather` with OA colors, `sync_crisalid_topics` |
| `app/graph/neo4j/document_dao.py` | **Modify** — new methods, 4th statement in transaction, `_hydrate` |
| `app/graph/neo4j/queries/sync_document_openalex_topics.cypher` | **Create** |
| `app/graph/neo4j/queries/sync_document_crisalid_topics.cypher` | **Create** |
| `app/graph/neo4j/queries/sync_documents_crisalid_topics_batch.cypher` | **Create** |
| `app/graph/neo4j/queries/get_document_topics_state.cypher` | **Create** |
| `app/graph/neo4j/queries/get_documents_for_topics_computation.cypher` | **Create** |
| `app/graph/neo4j/queries/count_documents_by_topics_state.cypher` | **Create** |
| `app/graph/neo4j/queries/get_document_by_uid.cypher` | **Modify** — collect `topics` |
| `app/amqp/amqp_document_event_message_factory.py` | **Modify** — `topics` in payload |
| `app/commands/documents.py` | **Modify** — `recompute-topics`, `recompute-topics-all` |
| `tests/fixtures/taxi_fixtures.py` | **Create** — autouse `CrisalidTaxiClient.match` mock |
| `tests/test_services/test_topics_input_builder.py` | **Create** |
| `tests/test_services/test_crisalid_taxi_client.py` | **Create** |
| `tests/test_services/test_topics_computation_service.py` | **Create** |
| `tests/test_graph/test_document_topics_dao.py` | **Create** |
| `tests/test_services/test_document_service.py`, `tests/test_amqp/...` | **Modify** — topics in computation and payload |

---

## Tests

Test env: an **autouse** fixture in `tests/fixtures/taxi_fixtures.py` patches
`CrisalidTaxiClient.match` with an `AsyncMock` returning a canned `TaxiMatchResponse` keyed on
input id (same role as `mock_unpaywall_service`), so the existing suites never open a socket.
Tests of the real client override it and patch `aiohttp.ClientSession` with the double
context-manager helper used in `tests/test_services/test_embedding_provider.py`. Settings are
patched via `get_app_settings` in the consuming module with `taxi_enabled=True`.

Input builder (unit, no DB):
- Priority order: `en` title present → `en` chosen even when `fr` abstract is longer; `fr` chosen
  when no `en` literal exists; `und` fallback only when no listed language matches; `None` when
  only `de` literals exist.
- `len(title + abstract) < 25` → `None`, even with many subjects.
- `alt_labels` never appear in the text; `pref_labels` deduplicated case-insensitively; only
  labels in the selected language are used.
- Same inputs → same hash; changing one character of the abstract changes the hash.

Client (unit):
- Payload contains `inputs` and `similarity_threshold` from settings; URL is
  `TAXI_API_URL + /api/v1/match/`; session created with `ClientTimeout(total=taxi_timeout_seconds)`.
- 500 → `None` + error log; `asyncio.TimeoutError` → `None`; malformed JSON → `None`.
- After `taxi_max_consecutive_failures` failures `is_open()` is true and `match()` returns `None`
  without calling `ClientSession`; after the deadline one call is attempted; a success resets the
  counter and closes the circuit.

Computation service (unit):
- Filters out `HAS_SUBFIELD`; drops `value < threshold`; keeps the top `taxi_max_topics` by
  score; empty matches → `TopicsResult` with empty `topics` (not `None`).
- `previous_hash == input_hash` → client not called; `force=True` → called anyway.
- `taxi_enabled=False` → client not instantiated.

DAO (integration, Neo4j, fixture `persisted_openalex_valid_hierarchy`):
- `sync_crisalid_topics` on a document that has one `openalex` edge and two stale `crisalid`
  edges: stale edges removed, `openalex` edge intact, new edges carry `source`, `score`, `model`,
  `computed_at`; node properties `topics_input_hash / topics_model / topics_computed_at` set.
- Unknown concept uid: not linked, absent from `linked_uids`, service logs a warning.
- Empty `topics`: edges wiped, hash written.
- `openalex` propagation: two source records with the same topic at scores 0.7 and 0.9 →
  one edge with `score = 0.9`; removing a source record and recomputing drops its topics.
- `get_document_by_uid` hydrates `Document.topics` with both sources.

Document service (integration):
- Unpaywall and Taxi mocks both applied after computation (OA status set **and** `crisalid`
  edges present) — verifies the `gather` path.
- Taxi mock returns `None`: document computed, `document_updated` emitted, previous `crisalid`
  edges and hash unchanged.
- Second computation with unchanged sources: Taxi mock not called.
- AMQP payload built by `AMQPDocumentEventMessageFactory` contains `topics` with `source`
  values `openalex` and `crisalid`.
