MERGE (s:SourceJournal {
  uid:               $source_journal_uid,
  source:            $source,
  source_identifier: $source_identifier
})
SET s.publisher = CASE WHEN $publisher IS NOT NULL THEN $publisher
  ELSE s.publisher
  END
SET s.titles = CASE WHEN $titles IS NOT NULL THEN $titles
  ELSE s.titles
  END
WITH s
FOREACH (identifier IN $identifiers |
  MERGE (j:JournalIdentifier {
    type:  identifier.type,
    value: identifier.value
  })
  MERGE (s)-[:HAS_IDENTIFIER]->(j)
)