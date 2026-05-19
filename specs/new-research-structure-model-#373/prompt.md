# Research structures refactoring

The aim is to restructure the management of research structures.

Please note that this refers to research structures, not the AuthorityOrganizations created for co-authors of publications from ROR repositories, etc., which are managed according to a different system but may share identifiers with research structures.

We’ll start by creating or updating the tests, assuming that the test Neo4j instance is running in the background.
The tests will cover different types of structures and the relationships between them, followed by updates, as if new AMQP messages had been received regarding these structures. In each case, verify the data created in the graph and ensure that the Pydantic entities are correctly populated by the DAOs.

## Current mode of operation

Until now, the pydantic types and node labels were only  ResearchUnit (for research units, i.e. laboratories) and Institution (for institutions)

### Research Structures

The research structures were created from AMQP messages by :
@/app/amqp/amqp_structure_message_processor.py

3 types of events were handled : created, updated, unchanged.

Example data : @/tests/data/organizations/research_unit_a_event.json

Identifiers of type "local" are (and will still be) tracking identifiers: when an event is received on a structure, they allow us to determine whether it is a creation or an update

The research units were created/updated by app/services/organizations/research_unit_service.py and app/graph/neo4j/research_unit_dao.py
The research units were assigned a UID calculated by `AgentIdentifierService.compute_uid_for` based on the code of the first identifier type (the first in the `research_unit_identifier_order` list in `app/settings/app_settings.py`). Generally, this was the ‘local’ type, i.e. the identifier used to link to the institution directory.

### Institutions

Institutions, on the other hand, were not created using data provided via messages. They were created when people were created or updated via `app/amqp/amqp_people_message_processor.py`, with the aim of implementing the ‘employed_at’ relationships between people and institutions .

In PeopleService app/services/people/people_service.py, the _update_employers_institutions method was used to dynamically create institutions as employers for individuals.
The data is provided by `app/services/organizations/institution_service.py`, an interface that calls upon the `InstitutionRegistryService` (`app/services/organizations/institution_registry_service.py`), which creates institutions using data provided by an external web service (a PostgreSQL API that utilises data from the government repository).

This procedure will remain in place only when a person created via a message will be employed by an institution that has not been described in a message provided by that institution; for example, an associate member of a laboratory whose employer is an institution that does not employ many of the laboratory’s researchers. But in most cases, institutions will be created through messages.

## New mode of operation

### Basic changes in AMQP messages

Now, there will be many more types of structures.
So the message will include the following fields:
- generic_type >> for the most general national type (national research directory generic subtypes)
- national_type >> for the specific national type (managed lists of national structure types, may evolve over time)
- local_types >> for local, unpredictable, arbitrary designations (literal with language tag) 

"names" and "acronym" are replaced by short_labels and long_labels, which are lists of literals with language tag.
The descriptions, identifiers and contact fields remain unchanged.

For now, ignore additional incoming fields like hceres_research_areas, erc_research_fields : they will be handled in another issue.

### New typologies

The new typology is more complex:

OrganizationBase
├── Institution
├── InstitutionSubdivision
├── UnitBase
│   ├── ResearchUnit
│   ├── SupportUnit
│   └── AdministrativeUnit
├── UnitSubdivision
└── Team

The mother class must be OrganizationBase. In the Neo4j graph, all organization structures will have the OrganizationUnit label, plus additional labels depending on their concrete type.

All organization structures must have:
- a mandatory generic_type
- either a national_type or at least one local_type

Use these enums:

class GenericOrganizationType(Enum):
    INSTITUTION = "institution"
    INSTITUTION_SUBDIVISION = "institution_subdivision"
    UNIT = "unit"
    UNIT_SUBDIVISION = "unit_subdivision"
    TEAM = "team"

class NationalOrganizationType(Enum):
    UNIV="UNIV"
    EPE = "EPE"
    EPST = "EPST"
    GE = "GE"
    COMUE="COMUE"
    UMR = "UMR"
    UAR = "UAR"
    UR = "UR"
    IRL="IRL"
    UFR="UFR"
    FAC="FAC"
    TEAM="TEAM"
    THEME="THEME"
    

class MissionType(Enum):
    RESEARCH = "research"
    SCIENTIFIC_SERVICES = "scientific_services"
    ADMINISTRATIVE_SERVICES = "administrative_services"
    TEACHING = "teaching"

The list of NationalOrganizationType values will evolve over time.

OrganizationBase must contain:

class OrganizationBase(BaseModel):
    generic_type: GenericOrganizationType
    national_type: Optional[NationalOrganizationType] = None
    local_types: list[Literal] = Field(default_factory=list)
    external: bool = False  # False = sourced from institutional directory; True = auto-created from registry

Add a model_validator ensuring that every organization has either national_type or at least one local_type.

Do not create allowed_national_types as a class variable on each unit class. Instead, use a central mapping:

ALLOWED_NATIONAL_TYPES_BY_GENERIC_TYPE = {
    GenericOrganizationType.INSTITUTION: {
    	NationalOrganizationType.EPE,
    	NationalOrganizationType.UNIV,
    	NationalOrganizationType.COMUE,
    	
    	},
    GenericOrganizationType.UNIT: {
        NationalOrganizationType.UMR,
        NationalOrganizationType.UAR,
        NationalOrganizationType.UR,
        NationalOrganizationType.IRL,
    },
    GenericOrganizationType.INSTITUTION_SUBDIVISION: {
        NationalOrganizationType.UFR,
        NationalOrganizationType.FAC,
    },
    GenericOrganizationType.UNIT_SUBDIVISION: set(),
    GenericOrganizationType.TEAM: {
        NationalOrganizationType.TEAM,
        NationalOrganizationType.THEME,
    },
}

Add a validator on OrganizationBase checking that national_type, when present, is allowed for the given generic_type.

Implement concrete non-unit classes:

class Institution(OrganizationBase):
    generic_type: TypingLiteral[GenericOrganizationType.INSTITUTION]

class InstitutionSubdivision(OrganizationBase):
    generic_type: TypingLiteral[GenericOrganizationType.INSTITUTION_SUBDIVISION]

class UnitSubdivision(OrganizationBase):
    generic_type: TypingLiteral[GenericOrganizationType.UNIT_SUBDIVISION]

class Team(OrganizationBase):
    generic_type: TypingLiteral[GenericOrganizationType.TEAM]

Do not create a concrete class named Unit. Use Unit as a type alias for the union of concrete unit classes.

Implement UnitBase:

class UnitBase(OrganizationBase):
    generic_type: TypingLiteral[GenericOrganizationType.UNIT]
    main_mission: MissionType
    secondary_missions: list[MissionType] = Field(default_factory=list)
    
main_mission is ignored or forbidden for non-units, and mandatory for units

The mandatory main_mission discriminates the concrete unit type:

class ResearchUnit(UnitBase):
    main_mission: TypingLiteral[MissionType.RESEARCH]

class SupportUnit(UnitBase):
    main_mission: TypingLiteral[MissionType.SCIENTIFIC_SERVICES]

class AdministrativeUnit(UnitBase):
    main_mission: TypingLiteral[MissionType.ADMINISTRATIVE_SERVICES]

class TeachingUnit(UnitBase):
    main_mission: TypingLiteral[MissionType.TEACHING]

Define:

Unit = Annotated[
    Union[
        ResearchUnit,
        SupportUnit,
        AdministrativeUnit,
        TeachingUnit,
    ],
    Field(discriminator="main_mission"),
]

Define OrganizationUnit as the global type union:

NonUnitOrganizationUnit = Annotated[
    Union[
        Institution,
        InstitutionSubdivision,
        UnitSubdivision,
        Team,
    ],
    Field(discriminator="generic_type"),
]

OrganizationUnit = Union[
    NonUnitOrganizationUnit,
    Unit,
]

Create module-level TypeAdapter instances for reuse — instantiating them once avoids repeated schema-building overhead:
unitAdapter = TypeAdapter(Unit)
nonUnitAdapter = TypeAdapter(NonUnitOrganizationUnit)
Do not create a TypeAdapter for OrganizationUnit directly — since it combines two unions with different discriminator fields, it cannot be validated reliably as a flat union. 
First inspect generic_type. If generic_type == "unit", validate with unitAdapter; otherwise validate with nonUnitAdapter.

### Relationships

We are now also establishing relationships between research structures.

There are two main types of relationship:
- inclusions (part_of): Strong relationships: Relationships of inclusion of certain institutions within EPE, of teams within units, and of a unit within an intermediate structure
- membership (member_of): Weak relationships : Supervisory relationships between institutions and research units, affiliation of teams with subdivisions of entities, participation of an entity in an intermediate structure


Incoming data have this format :

{         "type": "member_of", #mandatory
          "subtype": "main_supervision", # may be null
          "target": "local-EXAMPLE", # mandatory
          "start_date": "2000-01-01", # may be null
          "end_date": null # may be null
        }
        
Relationships are always created from children to parents: MEMBER_OF, PART_OF in the graph.
Relationships must be reified in Pydantic to carry attributes.
-memberships is a list of OrgMembership (start_date, end_date, position) --> MEMBER_OF
-parents is a list of OrgInclusion (start_date, end_date) --> PART_OF
When processing a relationship, you must:
- the ‘start_date’ and ‘end_date’ attributes must be added to the relationship
- Organization sub-type.
This should only be taken into account if the parent is an Institution and the child is a Unit. In this case, we are dealing with the French system of supervision. The position must be added (make a Pydantic enum of it)

### Relationship target resolution

Relationship targets follow two different rules depending on their uid prefix:

**local-xxx targets** (structures sourced from the institutional directory)
- Must have been created by a prior AMQP message before this one arrives.
- The service does **not** attempt to create them from any external source.
- If a local target is absent from the graph, the DAO logs an error and silently skips
  that relationship (the structure node itself is still created/updated).

**non-local targets** (uai-xxx, ror-xxx, …)
- May refer to institutions that have not yet been created by a message (e.g. a supervising
  institution described only in the national registry).
- Before persisting the structure, `OrganizationUnitService` checks whether each non-local
  target uid already exists in the graph.
- If not found, it calls `InstitutionService.create_institution(target_uid)` to fetch the
  institution from the external registry and persist it with `external=True`.
- If the registry lookup fails, a warning is logged and the relationship is skipped by the DAO
  (same behaviour as a missing local target). The structure itself is not blocked.

### external field

All organisation structures carry an `external: bool` field (default `False`):

- `False` — the structure was sourced from the institutional directory via an AMQP message.
- `True`  — the structure was auto-created from the external registry
  (`InstitutionRegistryService`) because it appeared as a relationship target.

The field is stored as a property on the `OrganizationUnit` Neo4j node and is round-tripped
through the DAO.

class OrgMembershipPosition(Enum):
    MAIN_SUPERVISION = "main_supervision"
    ASSOCIATED_SUPERVISION = "associated_supervision"
    PARTICIPATING_SUPERVISION = "participating_supervision"
    
### UID computation

The existing `AgentIdentifierService.compute_uid_for` method must be kept as the single mechanism for computing UIDs for all organization structures.

No backward compatibility with the previous ResearchUnit-only behavior is required.

Currently, `compute_uid_for` selects the first identifier type from a configured priority list, then looks for an identifier of that type in the entity identifiers. The UID is computed as:

```python
f"{selected_identifier.type.value}-{selected_identifier.value}"
````

For example:

```python
AgentIdentifier(type=OrganizationIdentifierType.LOCAL, value="CENTER-001")
```

produces:

```text
local-CENTER-001
```

The refactoring must generalize this behavior from `ResearchUnit` and `Institution` to all organization structures.

All concrete organization classes must therefore expose an `identifiers` field and must be compatible with `AgentIdentifierService.compute_uid_for`.

The existing organization-specific settings should be replaced or generalized. Instead of using separate settings such as:

```python
research_unit_identifier_order
institution_identifier_order
```

define a single identifier priority setting for all organization structures, for example:

```python
organization_identifier_order: list[OrganizationIdentifierType] = [
    OrganizationIdentifierType.LOCAL,
    OrganizationIdentifierType.UAI,
    OrganizationIdentifierType.ROR,
    OrganizationIdentifierType.IDREF,
]
```

The exact order should reflect the expected institutional data policy. In particular:

* `local` identifiers remain the preferred tracking identifiers for structures created or updated from AMQP messages.
* If a `local` identifier is present, the computed UID should normally be based on it.
* Other identifiers such as `uai`, `ror`, or `idref` will be used as fallback identifiers in the future when no local identifier is available.
* The selected identifier type and value must be stable over time, because the computed UID is used to decide whether the incoming structure corresponds to an existing node.

The `_get_identifier_order` method must be reworked so that all organization structure classes use the same organization identifier order.

The method should continue to distinguish `Person` from organization structures, but should no longer special-case only `ResearchUnit` and `Institution`.

For example, the logic should become conceptually equivalent to:

```python
if entity_cls.__name__ == "Person":
    return settings.person_identifier_order

if issubclass(entity_cls, OrganizationBase):
    return settings.organization_identifier_order
```

If no identifier matching the configured priority order is found, `compute_uid_for` must keep raising a `ValueError`, as it does today. This error should prevent the structure from being created, because a stable UID is mandatory for organization nodes.


### Create, update and unchanged event

The AMQP processor must continue to handle the three existing event types:

- `created`
- `updated`
- `unchanged`

The `unchanged` event must still be processed as a create-or-update operation.

This is intentional: even if the source system says that the structure is unchanged, the previous `created` or `updated` message may have been missed by this application. Therefore, `unchanged` must not be ignored.

The behavior should remain conceptually equivalent to the current logic:

```python
if event_type == "created":
    await self._create_structure(structure)
elif event_type == "updated":
    await self._update_structure(structure)
elif event_type == "unchanged":
    await self._create_or_update_structure(structure)
````

In the refactored implementation, this logic must apply to all organization structures, not only to `ResearchUnit`.

For `updated` events, the incoming message must be considered authoritative for the structure-owned data.

This means that an update replaces the current values of:

* labels: `short_labels`, `long_labels`, `descriptions`, `local_types`
* identifiers
* contacts
* organization-to-organization relationships: `PART_OF` and `MEMBER_OF`

If a label, identifier, contact, or organization relationship exists in the graph but is absent from the new message, it must be removed.

In particular, missing organization relationships in new messages must be deleted.

However, relationships from people to structures must not be deleted or replaced when processing a structure message.

The structure update must therefore preserve relationships such as:

* `(:Person)-[:MEMBER_OF]->(:OrganizationUnit)`
* `(:Person)-[:EMPLOYED_AT]->(:OrganizationUnit)`

These relationships are managed by the people ingestion workflow and must not be affected by organization structure messages.

Research structures themselves must not be deleted when they disappear from a message or when an update is processed. For now, the lifecycle of structures is not handled. Later, inactive or closed structures will be represented by an end date or lifecycle-related fields rather than by deleting the node.

So the expected behavior is:

* `created`: create the structure; if it already exists, handle as an `updated`
* `updated`: update the existing structure by replacing all structure-owned data from the incoming message, while preserving people-to-structure relationships. If it does not exist, handle as a `created`
* `unchanged`: create or update the structure, because previous messages may have been missed.
* missing labels, identifiers, contacts, and organization relationships in an authoritative update must be removed.
* organization nodes must not be deleted by this processor.

Do not delete the identifier nodes (AgentIdentifier), as they may be used by AuthorityOrganisations. When a research organisation shares identifiers with AuthorityOrganisations, no special action is required (this is a relationship that can be used in queries to link researchers’ affiliations with the affiliations they mention in the bylines of their publications).

###Neo4j setup

Update `app/graph/neo4j/neo4j_setup.py` for the new organization structure model.

Add a unique constraint on `OrganizationUnit.uid`.

Call this new constraint from `_create_constraints`.

This constraint must be the main UID uniqueness constraint for all research structures, because all organization structures now share the `OrganizationUnit` label.

Do not add separate UID constraints for each concrete organization type.

The `OrganizationUnit.uid` constraint must guarantee global UID uniqueness across:

* `Institution`
* `InstitutionSubdivision`
* `ResearchUnit`
* `SupportUnit`
* `AdministrativeUnit`
* `UnitSubdivision`
* `Team`

Keep the existing global `AgentIdentifier(type, value)` uniqueness constraint unchanged.

Add an index on `OrganizationUnit.generic_type`.

Add an index on `OrganizationUnit.national_type`.

The existing `Institution.uid` and `ResearchUnit.uid` constraints are no longer sufficient for the new model. The new `OrganizationUnit.uid` constraint must be used as the authoritative organization UID constraint.

Do not add uniqueness constraints on `MEMBER_OF` or `PART_OF` relationships for now, because these relationships carry temporal attributes and may later need historical versions.

Keep all unrelated constraints unchanged.

## Examples

### Institution subdivision creation example 


#### RabbitMQ message :

```json
{
  "structures_event": {
    "type": "created",
    "data": {
      "generic_type": "institution_subdivision",
      "type": "FAC",
      "local_types": [],
      "main_mission": null,
      "secondary_missions": null,
      "long_labels": [
        {
          "value": "Example Faculty of Sciences",
          "language": "en"
        },
        {
          "value": "Faculté des Sciences Exemple",
          "language": "fr"
        }
      ],
      "short_labels": [
        {
          "value": "Faculty Sciences",
          "language": "en"
        },
        {
          "value": "Fac Sciences",
          "language": "fr"
        }
      ],
      "descriptions": [
        {
          "value": "Example Faculty dedicated to scientific education and research.",
          "language": "en"
        },
        {
          "value": "Faculté exemple dédiée à l'enseignement et la recherche scientifique.",
          "language": "fr"
        }
      ],
      "identifiers": [
        {
          "type": "local",
          "value": "FAC-EXAMPLE-001"
        }
      ],
      "relationships": [
        {
          "type": "part_of",
          "target": "local-EXAMPLE-UNIV-001",
          "start_date": "2010-01-01",
          "end_date": "2030-12-31"
        }
      ],
      "contacts": []
    }
  }
}
```

#### Pydantic object :

```python

InstitutionSubdivision(

    uid="local-FAC-EXAMPLE-001",

    generic_type= "institution_subdivision"
    national_type= "FAC"
    local_types= []

    short_labels= [Literal(value:"Faculty Sciences", language:"en"), Literal(value:"Fac Sciences", language:"fr"\
)]
    long_labels= [Literal(value:"Example Faculty of Sciences", language:"en"), Literal(value:"Faculté des Sciences Exemple", language:"fr"\\
)]

    descriptions= [TextLiteral(value:"Example Faculty dedicated to scientific education and research.", language:"en"), TextLiteral(value:"Faculté exemple dédiée à l'enseignement et la recherche scientifique.", language:"fr")]
)
```

#### Neo4j graph :

##### Nodes :

```
(:OrganizationUnit:InstitutionSubdivision { uid: "local-FAC-EXAMPLE-001", generic_type: "institution_subdivision", national_type: "FAC" })

(:Literal {
value: "Example Faculty of Sciences",
language: "en",
type: "organization_long_label"
})

(:Literal {
value: "Faculté des Sciences Exemple",
language: "fr",
type: "organization_long_label"
})

(:Literal {
value: "Faculty Sciences",
language: "en",
type: "organization_short_label"
})

(:Literal {
value: "Fac Sciences",
language: "fr",
type: "organization_short_label"
})

(:TextLiteral {
value: "Example Faculty dedicated to scientific education and research.",
language: "en",
type: "organization_description"
})

(:TextLiteral {
value: "Faculté exemple dédiée à l'enseignement et la recherche scientifique.",
language: "fr",
type: "organization_description"
})
```

##### Relationships :

```
(:InstitutionSubdivision {uid:"local-FAC-EXAMPLE-001"})-[:HAS_LONG_LABEL]->(:Literal {value: "Example Faculty of Sciences"})

(:InstitutionSubdivision {uid:"local-FAC-EXAMPLE-001"})-[:HAS_LONG_LABEL]->(:Literal {value: "Faculté des Sciences Exemple"})

(:InstitutionSubdivision {uid:"local-FAC-EXAMPLE-001"})-[:HAS_SHORT_LABEL]->(:Literal {value: "Faculty Sciences"})

(:InstitutionSubdivision {uid:"local-FAC-EXAMPLE-001"})-[:HAS_SHORT_LABEL]->(:Literal {value: "Fac Sciences"})

(:InstitutionSubdivision {uid:"local-FAC-EXAMPLE-001"})-[:HAS_DESCRIPTION]->(:TextLiteral {value: "Example Faculty dedicated to scientific education and research."})

(:InstitutionSubdivision {uid:"local-FAC-EXAMPLE-001"})-[:HAS_DESCRIPTION]->(:TextLiteral {value: "Faculté exemple dédiée à l'enseignement et la recherche scientifique."})

(:InstitutionSubdivision {uid:"local-FAC-EXAMPLE-001"})
-[:PART_OF {start_date: date("2010-01-01"),end_date: date("2030-12-31")}]->(:OrganizationUnit {uid: "local-EXAMPLE-UNIV-001"})
```

### Unit creation example 

#### RabbitMQ message :

```json
{
  "structures_event": {
    "type": "unchanged",
    "data": {
      "generic_type": "unit",
      "type": "UMR",
      "local_types": [
        {
          "value": "Center",
          "language": "en"
        },
        {
          "value": "Centre",
          "language": "fr"
        }],
      "main_mission": "research",
      "secondary_missions": [],
      "long_labels": [
        {
          "value": "Example Research Center",
          "language": "en"
        },
        {
          "value": "Centre de recherche exemple",
          "language": "fr"
        }
      ],
      "short_labels": [
        {
          "value": "ERC",
          "language": "en"
        }
      ],
      "descriptions": [
        {
          "value": "Example description in English.",
          "language": "en"
        },
        {
          "value": "Description d'exemple en français.",
          "language": "fr"
        }
      ],
      "hceres_research_areas": [
        "ST6"
      ],
      "erc_research_fields": [],
      "hal_collection": "https://hal.science/EXAMPLE_COLLECTION",
      "contacts": [
        {
          "type": "postal_address",
          "format": "structured_physical_address",
          "value": {
            "country": "France",
            "zip_code": "00000",
            "city": "Example City",
            "street": "1 Example Street"
          }
        },
        {
          "type": "electronical_address",
          "format": "website_address",
          "value": {
            "uri": "https://www.example.org/"
          }
        }
      ],
      "identifiers": [
        {
          "type": "local",
          "value": "CENTER-001"
        },
        {
          "type": "nns",
          "value": "NNS-EXAMPLE"
        },
        {
          "type": "ror",
          "value": "ROR-EXAMPLE"
        }
      ],
      "relationships": [
        {
          "type": "member_of",
          "subtype": "main_supervision",
          "target": "local-EXAMPLE",
          "start_date": "2000-01-01",
          "end_date": null
        }
      ]
    }
  }
}
```

#### Pydantic object :

ResearchUnit(

    uid="local-CENTER-001",

    generic_type="unit"
    national_type="UMR"
    local_types=[
        Literal(value="Center", language="en"),
        Literal(value="Centre", language="fr"),
    ]

    main_mission="research"
    secondary_missions=[]
    
    parents:[]
    memberships=[OrgMembership(...)]

    research_areas=["ST6"]
    research_fields=[]
    hal_collection="https://hal.science/EXAMPLE_COLLECTION"

    short_labels=[
        Literal(value="ERC", language="en")
    ]

    long_labels=[
        Literal(value="Example Research Center", language="en"),
        Literal(value="Centre de recherche exemple", language="fr")
    ]

    descriptions=[
        TextLiteral(value="Example description in English.", language="en"),
        TextLiteral(value="Description d'exemple en français.", language="fr")
    ]
)

OrgMembership(
    position= "main_supervision",
    target= "local-EXAMPLE",
    start_date= "2000-01-01",
    end_date= null
)

#### Neo4j graph :

##### Nodes :

(:OrganizationUnit:Unit:ResearchUnit {
  uid: "local-CENTER-001",
  generic_type: "unit",
  national_type: "UMR",
  main_mission: "research",
  secondary_missions: [],
  research_areas: ["ST6"],
  research_fields: [],
  hal_collection: "https://hal.science/EXAMPLE_COLLECTION"
})



(:Literal {
value: "Centre",
language: "fr",
type: "organization_local_type"
})

(:Literal {
value: "Center",
language: "en",
type: "organization_local_type"
})

(:Literal {
value: "Example Research Center",
language: "en",
type: "organization_long_label"
})

(:Literal {
value: "Centre de recherche exemple",
language: "fr",
type: "organization_long_label"
})

(:Literal {
value: "ERC",
language: "en",
type: "organization_short_label"
})

(:TextLiteral {
value: "Example description in English.",
language: "en",
type: "organization_description"
})

(:TextLiteral {
value: "Description d'exemple en français.",
language: "fr",
type: "organization_description"
})

(:AgentIdentifier {
value: "CENTER-001",
type: "local"
})

(:AgentIdentifier {
value: "NNS-EXAMPLE",
type: "nns"
})

(:AgentIdentifier {
value: "ROR-EXAMPLE",
type: "ror"
})

(:StructuredPhysicalAddress {
uid: "<generated_or_hash_uid>"
})

(:Literal {value: "1 Example Street", language: "und", type: "institution_street_name"})

(:Literal {value: "Example City", language: "und", type: "institution_city_name"})

(:Literal {value: "00000", language: "und", type: "institution_zip_code"})

(:Literal {value: "France", language: "und", type: "institution_country_name"})

(:ElectronicalAddress {
uri: "https://www.example.org/"
})

##### Relationships :

(:OrganizationUnit:Unit:ResearchUnit {uid:"local-CENTER-001"})-[:HAS_LOCAL_TYPE]->(:Literal {value: "Center"...})

(:OrganizationUnit:Unit:ResearchUnit {uid:"local-CENTER-001"})-[:HAS_LONG_LABEL]->(:Literal {value: "Example Research Center"...})

(:OrganizationUnit:Unit:ResearchUnit {uid:"local-CENTER-001"})-[:HAS_LONG_LABEL]->(:Literal {value: "Centre de recherche exemple"...})

(:OrganizationUnit:Unit:ResearchUnit {uid:"local-CENTER-001"})-[:HAS_SHORT_LABEL]->(:Literal {value: "ERC"...})

(:OrganizationUnit:Unit:ResearchUnit {uid:"local-CENTER-001"})-[:HAS_DESCRIPTION]->(:TextLiteral {value: "Example description in English."...})

(:OrganizationUnit:Unit:ResearchUnit {uid:"local-CENTER-001"})-[:HAS_DESCRIPTION]->(:TextLiteral {value: "Description d'exemple en français"...})

(:OrganizationUnit:Unit:ResearchUnit {uid:"local-CENTER-001"})-[:HAS_IDENTIFIER]->(:AgentIdentifier {value: "CENTER-001", type: "local"})

(:OrganizationUnit:Unit:ResearchUnit {uid:"local-CENTER-001"})-[:HAS_IDENTIFIER]->(:AgentIdentifier {value: "NNS-EXAMPLE", type: "nns"})

(:OrganizationUnit:Unit:ResearchUnit {uid:"local-CENTER-001"})-[:HAS_IDENTIFIER]->(:AgentIdentifier {value: "ROR-EXAMPLE", type: "ror"})

(:OrganizationUnit:Unit:ResearchUnit {uid:"local-CENTER-001"})-[:HAS_ADDRESS]->(:StructuredPhysicalAddress)

(:StructuredPhysicalAddress)-[:HAS_STREET]->(:Literal {value: "1 Example Street"...})

(:StructuredPhysicalAddress)-[:HAS_CITY]->(:Literal {value: "Example City"...})

(:StructuredPhysicalAddress)-[:HAS_ZIP_CODE]->(:Literal {value: "00000"...})

(:StructuredPhysicalAddress)-[:HAS_COUNTRY]->(:Literal {value: "France"...})

(:OrganizationUnit:Unit:ResearchUnit {uid:"local-CENTER-001"})-[:HAS_ELECTRONICAL_ADDRESS]->(:ElectronicalAddress {uri: "https://www.example.org/"})

(:OrganizationUnit:Unit:ResearchUnit {uid:"local-CENTER-001"})
-[:MEMBER_OF {
    position: "main_supervision",
    start_date: date("2000-01-01"),
    end_date: null
}]->
(:OrganizationUnit:Institution {id: "uai-EXAMPLE"})

