CREATE (research_struct:Organisation:ResearchUnit {
  uid: $research_unit_uid,
  acronym: $acronym
})
WITH research_struct

FOREACH (name IN $names |
  MERGE (rs_name:Literal:Embeddable {
    value: trim(name.value),
    language: coalesce(nullif(trim(name.language), ''), 'und'),
    type: "research_unit_name"
  })
  ON CREATE SET rs_name.embedding_status = 'pending'
  MERGE (research_struct)-[:HAS_NAME]->(rs_name)
)

WITH research_struct
FOREACH (identifier IN $identifiers |
  MERGE (rs_identifier:AgentIdentifier {
    type: identifier.type,
    value: identifier.value
  })
  MERGE (research_struct)-[:HAS_IDENTIFIER]->(rs_identifier)
)

WITH research_struct
FOREACH (description IN $descriptions |
  MERGE (rs_description:Literal:Embeddable {
    value: trim(description.value),
    language: coalesce(nullif(trim(description.language), ''), 'und'),
    type: "research_unit_description"
  })
  ON CREATE SET rs_description.embedding_status = 'pending'
  MERGE (research_struct)-[:HAS_DESCRIPTION]->(rs_description)
);
