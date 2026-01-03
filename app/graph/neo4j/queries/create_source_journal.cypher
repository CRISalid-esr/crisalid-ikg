MERGE (s:SourceJournal { uid: $source_journal_uid })
ON CREATE SET
  s.source = $source,
  s.source_identifier = $source_identifier
ON MATCH SET
  s.source = coalesce(s.source, $source),
  s.source_identifier = coalesce(s.source_identifier, $source_identifier)

SET s.publisher = coalesce($publisher, s.publisher)
SET s.titles    = coalesce($titles, s.titles)

WITH s
FOREACH (identifier IN $identifiers |
  MERGE (j:JournalIdentifier { type: identifier.type, value: identifier.value })
  MERGE (s)-[:HAS_IDENTIFIER]->(j)
)
