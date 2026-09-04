# CRISalid institutional knowledge graph

CRISalid institutional Knowledge Graph (IKG) is a Python/FastAPI middleware that manages the data ingestion from the data bus and provides access to the graph through a GraphQL API.

CRISalid institutional Knowledge Graph (IKG) is distributed under the terms of the [CeCILL v2.1 license](http://www.cecill.info/licences/Licence_CeCILL_V2.1-fr.txt) (GPL compatible).

## Overview

### Goals

### Overall use

## Technical overview

### Used technologies

Server side :

- Python 3.10 with asyncio
- FastAPI with Pydantic
- Neo4j (community edition)
- RabbitMQ (through aio-pika)
- Poetry
- Pytest
- Black

## Development ressources (installation outside of a containerized environment)

### Basic requirements

Install Neo4j, RabbitMQ and the web server you want to use as a front-end.

#### RabbitMQ
Install RabbitMQ the first time in a container with the following command:
```bash
docker run -d --name rabbitmq   -p 5672:5672   -p 15672:15672   rabbitmq:3-management
```

The following times, simply start and stop the container with:
```bash
docker start rabbitmq
docker stop rabbitmq
```

#### Neo4j

Neo4j can be ran from the Neo4j Desktop interface.

To run Neo4j **in a container**, and **allow data persistence**, you can use the following command :

```bash
 docker run --publish=7474:7474 --publish=7687:7687 --env=NEO4J_AUTH=none -e NEO4J_apoc_export_file_enabled=true -e NEO4J_apoc_import_file_enabled=true -e NEO4J_apoc_import_file_use__neo4j__config=true -e NEO4J_PLUGINS=\[\"apoc\"\] -v ./neo4j/data:/data -v ./neo4j/logs:/logs -v ./neo4j/import:/import -v ./neo4j/backups:/backups -v ./neo4j/plugins:/plugins   neo4j:2026.06.0-community
```
If you want to run the container under heavy load, you can **increase the memory heap size** with the following command :

```bash
docker run --publish=7474:7474 --publish=7687:7687 --env=NEO4J_AUTH=none -e NEO4J_apoc_export_file_enabled=true -e NEO4J_server_memory_heap_initial__size=4G -e NEO4J_server_memory_heap_max__size=8G -e NEO4J_server_memory_pagecache_size=6G -e NEO4J_apoc_import_file_enabled=true -e NEO4J_apoc_import_file_use__neo4j__config=true -e NEO4J_PLUGINS=\[\"apoc\"\] -v ./neo4j/data:/data -v ./neo4j/logs:/logs -v ./neo4j/import:/import -v ./neo4j/backups:/backups -v ./neo4j/plugins:/plugins   neo4j:2026.06.0-community
```
###### Neo4j backup
With this approach, a **backup** can be **triggered** with the following command :

```bash
 docker run --interactive --tty --rm -v ./neo4j/data:/data -v ./neo4j/backups:/backups --env NEO4J_ACCEPT_LICENSE_AGREEMENT=yes neo4j/neo4j-admin:2026.06.0-community-debian neo4j-admin database dump neo4j --to-path=/backups  --overwrite-destination=true
```

The **backup can be restored** with the following command :

- if your backup file is in the `./neo4j/backups directory` (it was created with the previous command) :

```bash
 docker run --interactive --tty --rm -v ./neo4j/data:/data -v ./neo4j/backups:/backups --env NEO4J_ACCEPT_LICENSE_AGREEMENT=yes neo4j/neo4j-admin:2026.06.0-community-debian neo4j-admin database load neo4j --from-path=/backups   --overwrite-destination=true
```

- if your backup file is in another directory :

```bash
cat /path/to/my/neo4j.dump | docker run --interactive --rm -v ./neo4j/data:/data -v ./neo4j/backups:/backups --env NEO4J_ACCEPT_LICENSE_AGREEMENT=yes neo4j/neo4j-admin:2026.06.0-community-debian neo4j-admin database load neo4j --from-stdin --overwrite-destination=true
```

### Elasticsearch

To enable Elasticsearch support, you need to install Elasticsearch or to run it in a container. The following command will run an Elasticsearch instance :

```bash
docker run --publish=9200:9200 --publish=9300:9300 --env="discovery.type=single-node" --env="xpack.security.enabled=false" docker.elastic.co/elasticsearch/elasticsearch:8.15.2
```



### Embeddings (optional)

The application can compute and store embedding vectors on selected graph nodes (`Literal` and `TextLiteral` nodes whose type is semantically meaningful — titles, abstracts, labels, descriptions, etc.). These vectors are stored on nodes carrying the `:Embeddable` label and indexed in a Neo4j vector index, enabling semantic similarity search.

Embedding computation is **opt-in** and controlled by a single environment variable:

```env
EMBEDDING_ENABLED=true
```

When disabled (the default), the `:Embeddable` label is still applied to eligible nodes as they are created, so embeddings can be computed later without rebuilding the graph.

#### Configuration

Copy the embedding block from `.env.example` to your `.env` and adjust the values:

```env
EMBEDDING_ENABLED=true
EMBEDDING_PROVIDER=openai_compatible
EMBEDDING_API_URL="http://localhost:8081"
EMBEDDING_API_KEY=""
EMBEDDING_API_MODEL="intfloat/multilingual-e5-small"
EMBEDDING_DIMENSIONS=384
EMBEDDING_BATCH_SIZE=8
EMBEDDING_TIMEOUT_SECONDS=30
```

`EMBEDDING_DIMENSIONS` must match the output dimension of the model you use. `EMBEDDING_BATCH_SIZE` must not exceed the server's maximum batch size.

#### Running a local embedding server (TEI)

For development, [Hugging Face Text Embeddings Inference (TEI)](https://github.com/huggingface/text-embeddings-inference) is the recommended backend. It exposes an OpenAI-compatible `/v1/embeddings` endpoint that the `openai_compatible` provider uses directly.

```bash
model=intfloat/multilingual-e5-small
volume=$HOME/.cache/huggingface/tei

docker run --rm \
  --pull always \
  -p 8081:80 \
  -v "$volume:/data" \
  ghcr.io/huggingface/text-embeddings-inference:cpu-latest \
  --model-id "$model" \
  --max-batch-tokens 2048 \
  --max-client-batch-size 8
```

`intfloat/multilingual-e5-small` is a compact multilingual model (384 dimensions, ~120 MB) that works well for French and English academic text. It is downloaded automatically on first run into `~/.cache/huggingface/tei`.

Verify the server is up:

```bash
curl http://localhost:8081/health
# → "Ok"

curl http://localhost:8081/v1/embeddings \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{"model": "intfloat/multilingual-e5-small", "input": ["test sentence"]}'
```

#### How embeddings are computed

**Automatically (signal-driven path):** when embeddings are enabled, every write that produces embeddable nodes (document ingestion, structure creation, etc.) emits a `literal_updated` signal. `EmbeddingService` is connected to this signal at startup and processes all `pending` nodes in batches immediately after each write.

**Manually (CLI path):** use the `literals compute-embeddings` command to compute or recompute embeddings in bulk:

```bash
# Process all pending and failed nodes (default)
APP_ENV=DEV python -m app.cli literals compute-embeddings

# Process only specific literal types
APP_ENV=DEV python -m app.cli literals compute-embeddings --types document_title,document_abstract

# Recompute nodes not yet processed with the current model
APP_ENV=DEV python -m app.cli literals compute-embeddings --new-model intfloat/multilingual-e5-small

# Include already-successful nodes (full recompute)
APP_ENV=DEV python -m app.cli literals compute-embeddings --statuses pending,failed,success
```

#### Applying embeddings to an existing graph

If the graph was built with `EMBEDDING_ENABLED=false` (or before embedding support was added), nodes already carry the `:Embeddable` label with `embedding_status = "pending"`. No graph rebuild is needed — just run:

```bash
APP_ENV=DEV python -m app.cli literals compute-embeddings
```

This will process all pending nodes in batches and report counts before and after.

#### Changing the embedding model

If you switch to a model with a different output dimension, the existing vector index is incompatible and must be rebuilt. Use `--recreate-vector-indexes`, which resets all embedding properties, drops the index, recreates it with the new `EMBEDDING_DIMENSIONS`, and recomputes everything:

```bash
# Update EMBEDDING_API_MODEL and EMBEDDING_DIMENSIONS in .env first, then:
APP_ENV=DEV python -m app.cli literals compute-embeddings --recreate-vector-indexes
```

> **Warning:** `--recreate-vector-indexes` resets all embeddings and ignores `--statuses`. All nodes will be reprocessed.

#### Embedding status lifecycle

Each `:Embeddable` node carries an `embedding_status` property:

| Status | Meaning |
|---|---|
| `pending` | Node created or updated; embedding not yet computed |
| `success` | Embedding computed and stored; `embedding`, `embedding_hash`, `embedding_model` are set |
| `failed` | Provider call failed; `embedding_error` contains the reason |

Failed nodes are not retried automatically. Re-run `compute-embeddings` (default `--statuses pending,failed`) to retry them.

### Document topics via Crisalid-taxi (optional)

Each `Document` can be linked to OpenAlex `Topic` nodes with `HAS_TOPIC` relationships. Two sources coexist, distinguished by the `source` property of the relationship:

| `source` | Origin | Relationship properties |
|---|---|---|
| `openalex` | Propagated from the `HAS_TOPIC` edges of the document's source records (highest score wins) | `score` |
| `crisalid` | Computed by [Crisalid-taxi](https://github.com/CRISalid-esr/crisalid-taxi), a semantic classifier that embeds the document text and compares it with the OpenAlex taxonomy | `score`, `model`, `computed_at` |

The `openalex` propagation is always on. The Crisalid-taxi computation is **opt-in**:

```env
TAXI_ENABLED=true
```

Both require the OpenAlex taxonomy to be loaded in the graph (see `OPENALEX_TOPICS_TREE_PATH`).

#### Configuration

```env
TAXI_ENABLED=true
TAXI_API_URL="http://localhost:8000"
TAXI_TIMEOUT_SECONDS=30
TAXI_LANGUAGES=["en", "fr"]
TAXI_MIN_INPUT_LENGTH=25
TAXI_MAX_TOPICS=30
TAXI_SIMILARITY_THRESHOLD=0.6
TAXI_BATCH_SIZE=50
TAXI_MAX_CONSECUTIVE_FAILURES=5
TAXI_CIRCUIT_OPEN_SECONDS=300
```

- `TAXI_LANGUAGES` is a priority list: the first language that has a title or an abstract is used, and only the titles, abstracts and subject preferred labels in that language are sent. Literals with an undetermined language are used only when no listed language matches.
- `TAXI_MIN_INPUT_LENGTH` is the minimum length of title + abstract; shorter documents are not sent.
- `TAXI_SIMILARITY_THRESHOLD` is sent to Crisalid-taxi and re-applied on the returned scores; at most `TAXI_MAX_TOPICS` topics are kept per document.
- After `TAXI_MAX_CONSECUTIVE_FAILURES` consecutive failures (timeouts, 5xx…), calls are suspended for `TAXI_CIRCUIT_OPEN_SECONDS`, then retried.

#### How topics are computed

During document computation, the Crisalid-taxi call runs concurrently with the Unpaywall call, and the topics are written before the `document_created` / `document_updated` events are published, so the outbound messages contain them (`topics` key of the payload).

The text sent to Crisalid-taxi is hashed and stored on the document (`topics_input_hash`). When the title, abstract and subjects have not changed, Crisalid-taxi is not called again. A failed call never removes existing `crisalid` links.

#### Recomputing topics from the command line

```bash
# one document, ignoring the stored hash
python -m app.cli documents recompute-topics <document-uid>

# all documents whose text changed since the last computation, in batches
python -m app.cli documents recompute-topics-all

# only documents that never got crisalid topics
python -m app.cli documents recompute-topics-all --missing-only

# everything, e.g. after a Crisalid-taxi model change
python -m app.cli documents recompute-topics-all --force
```

`--batch-size` overrides `TAXI_BATCH_SIZE`; `--no-dispatch` disables the `document_updated` events emitted for documents whose topics changed. The command stops when the circuit breaker opens; rerun it later.

### Project and dependencies installation


Clone the projet, copy `.env.example` to `.env` and `.test.env` and update them. All the values defined in the app/settings classes (AppSettings, TestSettings, DevSettings...) can be overriden either through .env files or through environment variables (the latter takes precedence over the former).

If you want to use [poetry](https://python-poetry.org/) for dependency management.

```bash
poetry install
```
Note that poetry is not required as requirements are exported to requirements.txt.


### Dependencies export

Development dependencies can be exported to `requirements-dev.txt` file with the following command :

```bash
poetry export -f requirements.txt --output requirements-dev.txt --with=development
```

Production dependencies can be exported to `requirements.txt` file with the following command :

```bash
poetry export -f requirements.txt --output requirements.txt
```

### Tests

The project uses [pytest](https://docs.pytest.org/en/stable/) for testing.

Running the tests requires test dependencies to be running. The following command will launch Neo4j :

```bash
docker run --publish=7475:7474 --publish=7688:7687 --env=NEO4J_AUTH=none -e NEO4J_apoc_export_file_enabled=true -e NEO4J_apoc_import_file_enabled=true -e NEO4J_apoc_import_file_use__neo4j__config=true -e NEO4J_PLUGINS=\[\"apoc\"\]  neo4j:2026.06.0-community
```

The 7475 port is only intended to allow you to check test behaviour through the Neo4j browser. The 7688 port is the one used by the test suite to connect to the Neo4j instance. It should match the one defined in the `neo4j_uri` in `test_app_settings.py`, which can be overriden through `.test.env` or the `NEO4J_URI` environment variable.

To run the tests, from project root :

```bash
APP_ENV=TEST pytest
```

or with coverage

```bash
APP_ENV=TEST coverage run --source=app -m pytest
coverage report --show-missing
```

### Launch

From project root :

```bash
APP_ENV=DEV uvicorn app.main:app --reload
```

or

```bash
APP_ENV=DEV python3 app/main.py 
```

## Feeding the graph from the data bus

Open the rabbitMQ interface http://localhost:15672/
Default username/password are guest/guest.

Then publish messages in json format (examples below) in the corresponding queues (crisalid-ikg-structures, crisalid-ikg-people, crisalid-ikg-publications).
### Structure events

Here is an exemple of the payload of an incoming AMQP message for a structure event :

```json
{
  "structures_event": {
    "type": "unchanged",
    "data": {
      "names": [
        {
          "value": "Laboratoire de recherche fictif",
          "language": "fr"
        }
      ],
      "acronym": "",
      "descriptions": [
        {
          "value": "Un laboratoire de recherche fictif",
          "language": "fr"
        }
      ],
      "contacts": [
        {
          "type": "postal_address",
          "format": "structured_physical_address",
          "value": {
            "country": "France",
            "zip_code": "750000",
            "city": "PARIS",
            "street": "151 Rue Rémi Durant"
          }
        }
      ],
      "identifiers": [
        {
          "type": "local",
          "value": "UR0456"
        },
        {
          "type": "nns",
          "value": "201220011X"
        }
      ]
    }
  }
}
```

### People events

Here is an exemple of the payload of an incoming AMQP message for a people event :

```json
{
  "people_event": {
    "type": "unchanged",
    "data": {
      "names": [
        {
          "last_names": [
            {
              "value": "Caroy",
              "language": "fr"
            }
          ],
          "first_names": [
            {
              "value": "Jeanne",
              "language": "fr"
            }
          ]
        }
      ],
      "identifiers": [
        {
          "type": "local",
          "value": "jcaroy"
        }
      ],
      "memberships": [
        {
          "entity_uid": "local-UR0456"
        }
      ]
    }
  }
}
```

### Reference creation event

```json
{
  "reference_event": {
    "type": "created",
    "reference": 
    {
      "source_identifier": "doi10.0000/1234-5678/ad0cc0",
      "harvester": "scanr",
      "harvester_version": "1.2.0",
      "identifiers": [
        {
          "type": "doi",
          "value": "10.0000/1234-5678/ad0cc0"
        }
      ],
      "manifestations": [],
      "titles": [
        {
          "value": "A reference title",
          "language": "en"
        }
      ],
      "subtitles": [],
      "abstracts": [],
      "subjects": [
        {
          "uri": "http://www.idref.fr/02734004x/id",
          "dereferenced": false,
          "pref_labels": [
            {
              "value": "Analyse des donn\u00e9es",
              "language": null
            }
          ],
          "alt_labels": []
        },
        {
          "uri": "http://www.wikidata.org/entity/Q210521",
          "dereferenced": true,
          "pref_labels": [
            {
              "value": "r\u00e9solution num\u00e9rique",
              "language": "fr"
            },
            {
              "value": "image resolution",
              "language": "en"
            }
          ],
          "alt_labels": [
            {
              "value": "pixel count",
              "language": "en"
            }
          ]
        }
      ],
      "document_type": [
        {
          "uri": "http://purl.org/ontology/bibo/Article",
          "label": "Article"
        }
      ],
      "contributions": [
        {
          "rank": 0,
          "contributor": {
            "source": "scanr",
            "source_identifier": null,
            "name": "J. L. West",
            "name_variants": []
          },
          "role": "https://id.loc.gov/vocabulary/relators/aut.html",
          "affiliations": []
        },
        {
          "rank": 1,
          "contributor": {
            "source": "scanr",
            "source_identifier": null,
            "name": "N. Mahajan",
            "name_variants": []
          },
          "role": "https://id.loc.gov/vocabulary/relators/aut.html",
          "affiliations": []
        }
      ],
      "issue": {
        "source": "scanr",
        "source_identifier": "the_astrophysical_journal-ScanR",
        "titles": [],
        "volume": null,
        "number": [],
        "rights": null,
        "date": null,
        "journal": {
          "source": "scanr",
          "source_identifier": "0000-1111-2222-3333-the_astronomical_journal-american_astronomical_society-ScanR",
          "issn": [
            "0000-1111"
          ],
          "eissn": [],
          "issn_l": null,
          "publisher": "Publisher",
          "titles": [
            "Title1"
          ]
        }
      },
      "page": null,
      "book": null,
      "issued": "2023-12-01 00:00:00",
      "created": null,
      "version": 0
    },
    "enhanced": false
  },
  "entity": {
    "identifiers": [
      {
        "type": "orcid",
        "value": "0000-0001-2345-6789"
      }    ],
    "name": "Name"
  }
}
```
