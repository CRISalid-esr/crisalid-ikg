MATCH (s:SourcePerson {uid: $source_person_uid})
SET s.source = $source,
    s.source_identifier = $source_identifier,
    s.name = $name
WITH s
OPTIONAL MATCH (s)-[hi:HAS_IDENTIFIER]->(SourcePersonIdentifier)
DELETE hi
WITH s
FOREACH (identifier IN $identifiers |
  MERGE (i:SourcePersonIdentifier {
    type:  identifier.type,
    value: identifier.value
  })
  MERGE (s)-[:HAS_IDENTIFIER]->(i)
)