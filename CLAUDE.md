# CLAUDE.md

## Behaviour

## Git commits

- Commit messages must be short and to the point. A short bullet lists, no detailed explanations.
- Do not add a `Co-Authored-By` trailer or any other signature to commits.
- Do not add Claude.md
- Always run pylint before committing:
  ```bash
  pylint --rcfile=.pylintrc app/
  ```
  The score must not regress. Fix all E-level (error) issues; fix or suppress C/W/R issues with inline `# pylint: disable=<code>` comments when the warning is a false positive or acceptable trade-off.

## Application architecture

**CRISalid IKG** is a Python/FastAPI middleware that manages an institutional knowledge graph about research — researchers, structures, scholarly output, projects, and related entities.

### What it does

It acts as a central graph integration layer: it ingests entity events from upstream services (directory, harvesters), deduplicates and merges data, and publishes lifecycle events downstream. Data is stored as a graph in Neo4j; business objects are handled in memory as Pydantic models.

### Layer overview

```
External services (directory, harvesters, …)
        │  RabbitMQ messages
        ▼
AMQP layer  (app/amqp/)
  ├─ AMQPInterface — connection management, exchange/queue declarations, listener startup
  ├─ Topic message processors — one per domain (people, publications, structures, user actions, harvesting events)
  │    each processor decodes JSON, validates, calls services
  └─ AMQP message factories — build and publish outbound lifecycle events
        │  service calls
        ▼
Service layer  (app/services/)
  ├─ One service class per domain: PeopleService, DocumentService, ResearchUnitService, …
  ├─ Orchestrates business logic (merge strategies, equivalence, metadata computation, …)
  ├─ Calls DAOs for persistence; calls other services for cross-domain logic
  └─ Emits blinker signals on completion
        │  DAO calls / signals
        ▼
DAO / graph layer  (app/graph/)
  ├─ Generic DAO and DAOFactory interfaces — backend-agnostic
  ├─ Neo4j implementation — Neo4jDAOFactory maps entity types to concrete DAOs
  │    (PersonDAO, DocumentDAO, SourceRecordDAO, ResearchUnitDAO, …)
  └─ DAOs execute async Cypher queries; return (uid, Status) where Status ∈ {CREATED, UPDATED, DELETED, UNCHANGED}
        │  Cypher
        ▼
Neo4j database
```

Neo4j is the **only** implemented graph backend. It is accessed **exclusively** through DAOs — never directly from services or routes.

### Message-driven design

Although the app runs as a FastAPI process, the primary driver of work is **AMQP** (RabbitMQ), not HTTP. The five inbound topic queues are:

| Topic | Processor | Responsibility |
|---|---|---|
| People | `AMQPPeopleMessageProcessor` | Directory service person events |
| Publications | `AMQPReferenceMessageProcessor` | Harvester reference/publication events |
| Structures | `AMQPStructureMessageProcessor` | Research unit events |
| User actions | `AMQPUserActionsMessageProcessor` | Graph-side task requests |
| Harvesting events | `AMQPHarvestingEventsMessageProcessor` | Harvesting state and result notifications |

Each processor runs with configurable parallelism (default 10 workers). Inbound messages are placed on internal asyncio queues; workers pull from these queues and call services.

Outbound events are published by AMQP message factories, triggered by blinker signals (see below).

### Internal event / signal system

`app/signals.py` defines named **blinker** signals for every entity lifecycle:

- `person_created`, `person_updated`, `person_unchanged`, `person_deleted`, `person_identifiers_updated`
- `structure_created/updated/unchanged/deleted`, `institution_created/updated/unchanged/deleted`
- `document_created/updated/unchanged/deleted`, `document_created_from_sources`, `document_sources_changed`
- `source_record_created/updated`, `source_journal_created/updated/unchanged/deleted`
- `publications_to_be_updated`, `harvesting_state_event_received`, `harvesting_result_event_received`

Signal handlers are registered at startup in `CrisalidIKG.__init__` (app/crisalid_ikg.py). Key listener wiring:

- `document_sources_changed` / `document_created_from_sources` → `DocumentService` (recompute metadata, OA colors)
- `source_record_created/updated` → `EquivalenceService` (deduplication clustering) + `SourceRecordIndex` (Elasticsearch)
- All lifecycle signals → `AMQPInterface` (republish as outbound events)

Signals decouple processors from downstream business logic and allow multiple independent reactions to the same event.

### HTTP surface

The app exposes a small REST API (prefix `/api/v0/`) for querying entities:

- `/api/v0/person/` — people
- `/api/v0/organization/` — organizations
- `/api/v0/source_records/` — source records
- `/health/` — health check

HTTP is a secondary interface; it does not drive writes.

### CLI

`app/cli.py` is a **Typer** CLI with sub-commands grouped by domain:

```
people       — dispatch_event, dispatch_all
structures   — dispatch_event, dispatch_all
documents    — recompute_metadata, dispatch_event
source_records / source_journals — maintenance commands
```

CLI commands bootstrap the full app lifecycle (`@with_app_lifecycle` decorator initialises Neo4j and AMQP connections) and then manually fire signals or call services. This is the main tool for admin and testing operations.

### Neo4j setup

Schema setup runs once at startup via `Neo4jSetup.run()` (called from `setup_graph()` in `crisalid_ikg.py`). It creates all constraints inside a single write transaction using `CREATE CONSTRAINT IF NOT EXISTS`, so it is safe to run on every restart.

`Neo4jConnexion` is a thin async context manager — it opens a driver, yields it, then closes it. There is no long-lived connection singleton; each DAO operation acquires and releases a driver through this context manager.

Constraints are split into two tiers controlled by the `neo4j_edition` setting (default: `"community"`):

- **Community** — uniqueness constraints on `uid` for every node type (`Person`, `Document`, `SourceRecord`, `ResearchUnit`, `Institution`, `Journal`, `Concept`, …), composite uniqueness on identifier `(type, value)` pairs, and uniqueness on `Literal (value, language, type)`.
- **Enterprise only** — additionally: `NOT NULL` constraints on `AgentIdentifier.type` and `.value`; relationship uniqueness constraints on `HAS_NAME` and `REPRESENTED_BY` edges.

When adding a new node type or identifier type, a corresponding `CREATE CONSTRAINT` method must be added to `Neo4jSetup` and called from `_create_constraints`.

### Testing

Tests require a running Neo4j instance. The user starts it outside the IDE:

```bash
docker run --publish=7475:7474 --publish=7688:7687 --env=NEO4J_AUTH=none \
  -e NEO4J_apoc_export_file_enabled=true \
  -e NEO4J_apoc_import_file_enabled=true \
  -e NEO4J_apoc_import_file_use__neo4j__config=true \
  -e NEO4JLABS_PLUGINS='["apoc"]' \
  neo4j:5-community
```

Before running tests, check that the instance is reachable. If it is not running, stop and ask the user to start it — do not attempt to start it yourself.

```bash
# Run all tests
APP_ENV=TEST pytest

# Run specific tests
# Add `import pytest` and `@pytest.mark.current` to the target test functions, then:
APP_ENV=TEST pytest -m current
# Always run from the project root. 
# Always remove @pytest.mark.current before committing.
```

### Key conventions

- All I/O (Neo4j, AMQP, HTTP clients) is **async/await**.
- Pydantic models are defined in `app/models/`; they are the only way data travels between layers.
- Settings are environment-specific subclasses in `app/settings/`; selected via `APP_ENV`.
- Elasticsearch indexing is optional (`es_enabled` setting) and is secondary to the graph.

