MERGE (s:SourcePerson { uid: $source_person_uid })
ON CREATE SET
  s.source = $source,
  s.name   = $name
ON MATCH SET
  s.source = coalesce($source, s.source),
  s.name   = coalesce($name, s.name)

SET s.source_identifier = $source_identifier,
    s.first_name        = $first_name,
    s.last_name         = $last_name,
    s.name_variants     = $name_variants

WITH s
FOREACH (identifier IN $identifiers |
  MERGE (i:SourcePersonIdentifier { type: identifier.type, value: identifier.value })
  MERGE (s)-[:HAS_IDENTIFIER]->(i)
)
