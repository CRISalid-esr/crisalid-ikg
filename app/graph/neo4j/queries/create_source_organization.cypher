MERGE (s:SourceOrganization:${dynamicLabel} {
  uid:    $source_organization_uid,
  source: $source,
  name:   $name,
  type:   $type
})
SET s.source_identifier = $source_identifier
WITH s
FOREACH (identifier IN $identifiers |
  MERGE (i:SourceOrganizationIdentifier {
    type:  identifier.type,
    value: identifier.value
  })
  MERGE (s)-[:HAS_IDENTIFIER]->(i)
)