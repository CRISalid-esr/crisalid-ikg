MERGE (s:SourceOrganization:${dynamicLabel} { uid: $source_organization_uid })
ON CREATE SET
  s.source = $source,
  s.name   = $name,
  s.type   = $type
ON MATCH SET
  s.source = coalesce($source, s.source),
  s.name   = coalesce($name, s.name),
  s.type   = coalesce($type, s.type)

SET s.source_identifier = $source_identifier

WITH s
FOREACH (identifier IN $identifiers |
  MERGE (i:SourceOrganizationIdentifier {
    type:  identifier.type,
    value: identifier.value
  })
  FOREACH (_ IN CASE
    WHEN identifier.extra_information IS NOT NULL
         AND identifier.extra_information <> '{}'
         AND identifier.extra_information <> 'null'
    THEN [1]
    ELSE []
  END |
    SET i.extra_information = identifier.extra_information
  )

  MERGE (s)-[:HAS_IDENTIFIER]->(i)
)
