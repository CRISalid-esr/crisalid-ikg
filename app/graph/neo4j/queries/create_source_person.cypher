MERGE (s:SourcePerson {
  uid:    $source_person_uid,
  source: $source,
  name:   $name
})
SET s.source_identifier = $source_identifier,
s.first_name = $first_name,
s.last_name = $last_name,
s.name_variants = $name_variants
WITH s
FOREACH (identifier IN $identifiers |
  MERGE (i:SourcePersonIdentifier {
    type:  identifier.type,
    value: identifier.value
  })
  MERGE (s)-[:HAS_IDENTIFIER]->(i)
)