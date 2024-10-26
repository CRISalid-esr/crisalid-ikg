MATCH (s:SourceJournal {uid: $source_journal_uid})
SET s.source = $source,
    s.source_identifier = $source_identifier,
    s.publisher = $publisher,
    s.titles = $titles
WITH s
OPTIONAL MATCH (s)-[hi:HAS_IDENTIFIER]->(JournalIdentifier)
DELETE hi
WITH s
FOREACH (identifier IN $identifiers |
  MERGE (j:JournalIdentifier {
    type:  identifier.type,
    value: identifier.value
  })
  MERGE (s)-[:HAS_IDENTIFIER]->(j)
)