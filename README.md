# CRISalid institutional knowledge graph

CRISalid institutional Knowledge Graph (IKG) is a Python/FastAPI middleware that manages the data ingestion from the
data bus and provides access to the graph through a GraphQL API.

CRISalid institutional Knowledge Graph (IKG) is distributed under the terms of
the [CeCILL v2.1 license](http://www.cecill.info/licences/Licence_CeCILL_V2.1-fr.txt) (GPL compatible).

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

Install Postgresql, RabbitMQ and the web server you want to use as a front-end.

Note that poetry is not required as requirements are exported to requirements.txt.

Clone the projet, copy .env.example to .env and .test.env and update them. All the values defined in the app/settings
classes (AppSettings, TestSettings, DevSettings...)
can be overriden either through .env files or through environment variables (the latter takes precedence over the
former).

### Dependencies installation

The project uses [poetry](https://python-poetry.org/) for dependency management.

```bash
poetry install
```

### Dependencies export

Development dependencies can be exported to requirements-dev.txt file with the following command :

```bash
poetry export -f requirements.txt --output requirements-dev.txt --with=development
```

Production dependencies can be exported to requirements.txt file with the following command :

```bash
poetry export -f requirements.txt --output requirements.txt
```

### Tests

The project uses [pytest](https://docs.pytest.org/en/stable/) for testing.

Running the tests requires test dependencies to be installed. The following command will install them :

#### Neo4j 

```bash
docker run --publish=7475:7474 --publish=7688:7687 --env=NEO4J_AUTH=none   neo4j:5-community
```

The 7475 port is only intended to allow you to check test behaviour through the Neo4j browser.
The 7688 port is the one used by the test suite to connect to the Neo4j instance. It should match the one defined in the
neo4j_uri in test_app_settings.py, which can be overriden through .test.env or
the NEO4J_URI environment variable.

#### Elasticsearch

```bash
docker run --publish=9201:9200 --publish=9301:9300 --env="discovery.type=single-node" --env="xpack.security.enabled=false" docker.elastic.co/elasticsearch/elasticsearch:8.15.2
```
From project root :

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
          "type": "RNSR",
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