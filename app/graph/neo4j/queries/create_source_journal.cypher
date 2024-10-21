CREATE (s:SourceJournal {
  uid:               $source_journal_uid,
  source:            $source,
  source_identifier: $source_identifier,
  publisher:         $publisher,
  titles:            $titles
})
WITH s
UNWIND $identifiers AS identifier
CREATE (j:JournalIdentifier {
  type:  identifier.type,
  value: identifier.value
})
CREATE (s)-[:HAS_IDENTIFIER]->(j)