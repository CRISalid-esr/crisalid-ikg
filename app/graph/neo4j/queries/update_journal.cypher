MATCH (s:Journal {uid: $journal_uid})
SET s.issn_l = $issn_l,
s.titles = $titles,
s.publisher = $publisher
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