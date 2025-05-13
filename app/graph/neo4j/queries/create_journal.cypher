MERGE (s:Journal {
  uid:               $journal_uid,
  issn_l:            $issn_l
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
  SET j.last_checked = identifier.last_checked
  SET j.format = identifier.format
)