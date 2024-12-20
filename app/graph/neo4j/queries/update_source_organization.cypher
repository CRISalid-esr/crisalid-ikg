MATCH (s:SourceOrganization:${dynamicLabel} { uid: $source_organization_uid })
SET s.source = $source,
    s.source_identifier = $source_identifier,
    s.name = $name,
    s.type = $type
WITH s
OPTIONAL MATCH (s)-[rel:HAS_IDENTIFIER]->(i:SourceOrganizationIdentifier)
WHERE NOT i.type + ':' + i.value IN $identifier_composite_keys
DELETE rel, i
WITH s
FOREACH (identifier IN $identifiers |
  MERGE (i:SourceOrganizationIdentifier {
    type: identifier.type,
    value: identifier.value
  })
  MERGE (s)-[:HAS_IDENTIFIER]->(i)
)
