MERGE (s:SourceRecord {uid: $source_record_uid})
  ON CREATE SET s.harvester = $harvester, s.source_identifier = $source_identifier
WITH s
FOREACH (title IN $titles |
  MERGE (s)-[:HAS_TITLE]->(t:Literal {value: title.value, language: title.language})
)
FOREACH (abstract IN $abstracts |
  MERGE (s)-[:HAS_ABSTRACT]->(a:Literal {value: abstract.value, language: abstract.language})
)
FOREACH (identifier IN $identifiers |
  MERGE (i:PublicationIdentifier {type: identifier.type, value: identifier.value})
  MERGE (s)-[:HAS_IDENTIFIER]->(i)
)
WITH s
FOREACH (_ IN CASE WHEN $issue IS NOT NULL THEN [1] ELSE [] END |
  MERGE (i:SourceIssue {source_identifier: $issue.source_identifier})
  ON CREATE SET i.source = $issue.source, i.volume = $issue.volume, i.number = $issue.number, i.rights = $issue.rights, i.date = $issue.date, i.titles = $issue.titles
  ON MATCH SET  i.source = $issue.source, i.volume = $issue.volume, i.number = $issue.number, i.rights = $issue.rights, i.date = $issue.date, i.titles = $issue.titles
  MERGE (s)-[:PUBLISHED_IN]->(i)

  FOREACH (_ IN CASE WHEN $journal_uid IS NOT NULL THEN [1] ELSE [] END |
    MERGE (j:SourceJournal {uid: $journal_uid})
    MERGE (i)-[:ISSUED_BY]->(j)
  )
)

WITH s, $person_uid AS person_uid
MATCH (p:Person {uid: person_uid})
MERGE (s)-[:HARVESTED_FOR]->(p)


WITH s, $subject_uris AS subject_uris
UNWIND subject_uris AS subject_uri
MATCH (sub:Concept {uri: subject_uri})
MERGE (s)-[:HAS_SUBJECT]->(sub)
