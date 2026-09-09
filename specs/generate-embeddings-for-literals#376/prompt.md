# Add Embeddings for Selected `Literal` and `TextLiteral` Nodes

## Goal

Add embedding support for selected `Literal` and `TextLiteral` nodes in the Neo4j graph.

When a relevant `Literal` or `TextLiteral` node is created or updated, it must eventually receive an `embedding` property containing the embedding vector of its `value`. (`TextLiteral` nodes are literals whose `value` may be too long to be deduplicated using a `language`/`value` Neo4j constraint. They therefore have a `key` property containing a SHA-256 hash.)

Embeddings are computed from the `value` property only.

The embedding hash is also computed from the `value` property only.

## Architecture: `Embeddable` Label

To cleanly separate concerns between *which nodes are eligible for embedding* and *how embeddings are computed*, introduce a dedicated Neo4j label:

```text
Embeddable
```

Any `Literal` or `TextLiteral` node whose `type` is in the embeddable type list (see below) must additionally carry the `Embeddable` label. Nodes whose `type` is not embeddable must not carry this label.

- In **all Cypher queries** that create or merge a `Literal` or `TextLiteral` node, the `Embeddable` label must be **hardcoded** in the query when the node's `type` belongs to the embeddable type list.
- Conversely, queries that create non-embeddable literals must not apply the `Embeddable` label.
- The mapping from `type` → `Embeddable` label is fixed at the Cypher level; there must be no runtime decision involving the embedding configuration to decide whether to apply the label.
- The `Embeddable` label is independent from the `ENABLE_EMBEDDINGS` feature flag: nodes are labelled `Embeddable` regardless of whether embeddings are currently enabled.

During Neo4j setup, add a command to add the ‘Embeddable’ label (if it does not already exist) to the Literal/TextLiteral types of all embeddable types (for migration purposes)

The embedding computation process operates exclusively on nodes carrying the `Embeddable` label.

- All embedding-related Cypher queries (selecting pending nodes, updating embedding properties, creating vector indexes, etc.) target the `Embeddable` label only.
- The embedding computation logic does not care about literal `type`, except when filtering is explicitly requested via the CLI (e.g. `--types`).
- A single vector index is created on `Embeddable.embedding` (see "Neo4j Vector Indexes" below).

## Embeddable Literal Types

Only `Literal` and `TextLiteral` nodes whose `type` is in the following list are `Embeddable`:

```
    "organization_long_label",
    "organization_description",
    "research_unit_name",
    "research_unit_description",
    "institution_name",
    "institution_country_name",
    "concept_pref_label",
    "document_title",
    "document_abstract",
    "concept_alt_label",
    "authority_organization_state_name",
    "institution_state_name",
    "institution_continent_name",
    "concept_definition",
```

The following types must not be `Embeddable`:

```
    "organization_short_label",
    "institution_street_name",
    "institution_city_name",
    "institution_zip_code",
    "person_first_name",
    "person_last_name",
    "source_record_abstract",
    "source_record_title",
```

## Node Properties

`Embeddable` nodes (i.e. `Literal:Embeddable` or `TextLiteral:Embeddable`) must use the following properties:

```text
embedding: list[float]
embedding_status: "pending" | "success" | "failed" # use an enum instead
embedding_hash: string
embedding_model: string
embedding_updated_at: datetime
embedding_error: string | null
```

`embedding_status` must default to:

```text
pending
```

## Embedding Status Lifecycle

When an `Embeddable` node is created or updated, set:

```text
embedding_status = "pending" # use the enum instead
```

A `literal_updated` signal must then be emitted.

The signal does not need to contain all pending literal IDs. It may simply notify the embedding update service that pending `Embeddable` nodes exist.

The embedding update service must then process all nodes carrying the `Embeddable` label whose:

```text
embedding_status = "pending"
```

For each pending node:

1. Compute the current hash from the node `value`.

2. If all of the following are true:

   * `embedding` exists
   * `embedding_hash` equals the current hash
   * `embedding_model` equals the currently configured embedding model

   then set:

   ```text
   embedding_status = "success"
   ```

3. Otherwise, compute a new embedding from the node `value`.

4. If embedding computation succeeds, update:

   ```text
   embedding = <computed vector>
   embedding_hash = <current value hash>
   embedding_model = <current embedding model>
   embedding_updated_at = <current datetime>
   embedding_status = "success"
   embedding_error = null
   ```

5. If embedding computation fails or times out, update:

   ```text
   embedding_status = "failed"
   embedding_error = <error message>
   ```

Do not implement automatic retry logic for failed embeddings. Failed embeddings will be retried manually using the CLI bulk command.

## Bulk Embedding CLI Command

Add the following command to the CLI:

```bash
cli literals compute-embeddings
```

This command calculates or recalculates embeddings in bulk for `Embeddable` nodes.

It must work even on a graph where embedding properties do not yet exist.

The command must support the following optional parameters:

```text
--types
```

List of literal `type` values to process. The command still operates only on `Embeddable` nodes; `--types` further restricts which embeddable types are processed.

Example:

```bash
cli literals compute-embeddings --types document_title,document_abstract
```

```text
--new-model
```

Only process `Embeddable` nodes whose embeddings were not calculated using this model.

This allows recomputing embeddings when the embedding model changes.

```text
--statuses
```

List of embedding statuses to process.

Default:

```text
pending,failed
```

It must also be possible to include `success` in order to recompute embeddings that were previously computed successfully.

Example:

```bash
cli literals compute-embeddings --statuses success
```

This command must allow:

* computing missing and/or failed embeddings
* recomputing all embeddings using a new model
* initializing embeddings on an existing graph (where related properties — embedding, embedding_hash, etc. — do not even exist)

## Embedding Feature Flag

Embedding *computation* must be globally controlled by the environment variable:

```env
EMBEDDING_ENABLED=true
```

If `EMBEDDING_ENABLED` is not set to `true`, embedding computation is disabled globally.

When embeddings are disabled:

- embedding-related processing signals will have no effects (listeners are not registered)
- the CLI embedding command will abort with a significant message

The labelling process (applying the `Embeddable` label in Cypher queries) is **not** affected by this flag. Nodes continue to be labelled `Embeddable` so that embeddings can be computed later once the flag is enabled.

## Embedding Providers

[Examples of scripts that do this are provided in our graphrag-experiments project in /home/joachim/code/graphrag-experiments/scripts, but these are command-line scripts designed to calculate embeddings in bulk with a model running locally. At the time they were designed, the literals in the graph did not have a type yet, and there was no distinction between literal and textliteral]

The application must support several embedding computation strategies through a provider abstraction.

Create an `EmbeddingProvider` interface with an async method similar to:

```python
async def embed_texts(self, texts: list[str]) -> list[list[float]]:
    ...
```

The implementation must use a factory-style design selected by an environment variable:

```env
EMBEDDING_PROVIDER=...
```

Supported providers should include at least:

```text
openai_compatible
sentence_transformer
```

### OpenAI-Compatible Provider

This provider calls a remote or local HTTP service exposing an OpenAI-compatible embeddings API.

It must be configurable with:

```env
EMBEDDING_API_URL=...
EMBEDDING_API_KEY=...
EMBEDDING_API_MODEL=...
EMBEDDING_DIMENSIONS=... # required for Neo4j setup
```

This provider must be usable with:

* OpenAI-compatible remote embedding services
* vLLM embedding endpoints
* Hugging Face Text Embeddings Inference if exposed through a compatible API

At development time, we will use Hugging Face Text Embeddings Inference.

```
model=intfloat/multilingual-e5-small
volume=$HOME/.cache/huggingface/tei

docker run --rm \
  --pull always \
  -p 8080:80 \
  -v "$volume:/data" \
  ghcr.io/huggingface/text-embeddings-inference:cpu-latest \
  --model-id "$model" \
  --max-batch-tokens 2048 \
  --max-client-batch-size 8
```

Example use : 
```
curl 127.0.0.1:8080/embed \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{"inputs":["query: histoire économique de la France","passage: Ce document analyse les transformations économiques françaises."]}'
```

Reference:

```text
https://github.com/huggingface/text-embeddings-inference#get-started
```

### SentenceTransformer Provider

>>>> Just plan for it to be present in the design, and add the class with empty methods 

This provider uses a local `sentence-transformers` model.

It must be configurable with variables such as:

```env
EMBEDDING_LOCAL_MODEL=...
EMBEDDING_DEVICE=cpu
```

or:

```env
EMBEDDING_DEVICE=cuda
```

The provider must not block the FastAPI event loop.

## Provider Loading Requirements

Only the libraries and models required by the configured provider must be imported and loaded into RAM.

For example:

* if `EMBEDDING_PROVIDER=openai_compatible`, do not import or initialize `sentence_transformers`
* if `EMBEDDING_PROVIDER=sentence_transformer`, load the local model only once and reuse it

If a required variable for the selected provider is missing, the application must log an explicit configuration error.

## Batch Processing

Pending `Embeddable` nodes must be processed in batches.

The batch size must be configurable, for example:

```env
EMBEDDING_BATCH_SIZE=64
```

Embedding requests must also have a configurable timeout:

```env
EMBEDDING_TIMEOUT_SECONDS=30
```

Failures in one node or one batch must not stop the whole embedding process.

Failed nodes must be marked with:

```text
embedding_status = "failed"
embedding_error = <error message>
```

No automatic retry logic is required.

## Neo4j Vector Indexes

Reference: https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/

Create a **single** Neo4j vector index on the `Embeddable` label as part of this task.

The index must be created idempotently during graph setup using `CREATE VECTOR INDEX ... IF NOT EXISTS`.

Because both `Literal` and `TextLiteral` embeddable nodes carry the `Embeddable` label, a single vector index on `Embeddable.embedding` covers both. Do not create separate indexes for `Literal.embedding` and `TextLiteral.embedding`.

The vector index configuration must use:

```text
vector.dimensions = <configured embedding dimension>
vector.similarity_function = "cosine"
```

The embedding dimension must be configurable because it depends on the selected embedding model.

Add an environment variable such as:

```env
EMBEDDING_DIMENSIONS=384
```

The value of `EMBEDDING_DIMENSIONS` must match the dimension returned by the configured embedding provider.

Use Cypher similar to:

```cypher
CREATE VECTOR INDEX embeddable_embedding IF NOT EXISTS
FOR (n:Embeddable)
ON n.embedding
OPTIONS {indexConfig: {
  `vector.dimensions`: $embedding_dimensions,
  `vector.similarity_function`: 'cosine'
}}
```

Do not create separate vector indexes per literal `type` in this task. Filtering by literal `type` must be handled at query time or by post-filtering results.

The implementation must use Neo4j's current vector index syntax. Neo4j's documentation recommends specifying `vector.dimensions`, because it ensures only vectors of that size are indexed and makes dimension mismatches explicit; `cosine` is the usual similarity function for text embeddings. Vector indexes are created asynchronously, and their state can be checked with `SHOW INDEXES WHERE type = "VECTOR"`.

## Embedding Model Changes and Vector Index Migration

Changing the embedding model may change the embedding dimension. It is the user's responsibility to include the `--recreate-vector-indexes` option in the command if they change the dimensions of the model being used.

Example:

```bash
cli literals compute-embeddings \
  --new-model <new_model> \
  --recreate-vector-indexes
```

The `--recreate-vector-indexes` flag is not compatible with status filters, as it will reset all embedding statuses to `"pending"`.

If the dimension has changed:

- the existing vector index is no longer compatible
- embeddings produced by the previous model must not be mixed with embeddings produced by the new model in the same indexed property
- the application must run an explicit embedding migration

The migration must:

1. Reset all embedding values on `Embeddable` nodes:
   ```text
   embedding = null
   embedding_hash = null
   embedding_model = # keep previous value
   embedding_status = "pending"
   embedding_updated_at = # keep previous value
   embedding_error = null
   ```
2. Drop the existing vector index on `Embeddable.embedding`.
3. Recreate the vector index using the new `EMBEDDING_DIMENSIONS`.
4. Recompute embeddings using the newly configured model:
   ```text
   embedding = <newly computed vector>
   embedding_hash = <hash of value>
   embedding_model = <new embedding model>
   embedding_status = "success"
   embedding_updated_at = <current datetime>
   embedding_error = null
   ```