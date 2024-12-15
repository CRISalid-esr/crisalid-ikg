MERGE (s:SourcePerson {
  uid:               $source_person_uid,
  source:            $source,
  source_identifier: $source_identifier,
  name:              $name
})
WITH s
FOREACH (identifier IN $identifiers |
  MERGE (i:SourcePersonIdentifier {
    type:  identifier.type,
    value: identifier.value
  })
  MERGE (s)-[:HAS_IDENTIFIER]->(i)
)