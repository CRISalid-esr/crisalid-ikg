MATCH (s:SourceJournal {uid: $source_journal_uid})
SET s.source = $source,
    s.source_identifier = $source_identifier,
    s.publisher = $publisher,
    s.titles = $titles
WITH s
OPTIONAL MATCH (s)-[hi:HAS_IDENTIFIER]->(JournalIdentifier)
DELETE hi
WITH s
UNWIND $identifiers AS identifier
CREATE (j:JournalIdentifier {
  type:  identifier.type,
  value: identifier.value
})
CREATE (s)-[:HAS_IDENTIFIER]->(j)