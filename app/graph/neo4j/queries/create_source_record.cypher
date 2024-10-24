CREATE (s:SourceRecord {uid: $source_record_uid, harvester: $harvester, source_identifier: $source_identifier})
WITH s
FOREACH (title IN $titles |
  CREATE (t:Literal {value: title.value, language: title.language})
  CREATE (s)-[:HAS_TITLE]->(t)
)
FOREACH (abstract IN $abstracts |
  CREATE (a:Literal {value: abstract.value, language: abstract.language})
  CREATE (s)-[:HAS_ABSTRACT]->(a)
)
FOREACH (identifier IN $identifiers |
  MERGE (i:PublicationIdentifier {type: identifier.type, value: identifier.value})
  MERGE (s)-[:HAS_IDENTIFIER]->(i)
)
WITH s, $issue AS issue, $journal_uid AS journal_uid

FOREACH (_ IN CASE WHEN issue IS NOT NULL THEN [1] ELSE [] END |
  MERGE (i:SourceIssue {source_identifier: issue.source_identifier})
  ON CREATE SET i.source = issue.source, i.volume = issue.volume, i.number = issue.number, i.rights = issue.rights, i.date = issue.date, i.titles = issue.titles
  ON MATCH SET  i.source = issue.source, i.volume = issue.volume, i.number = issue.number, i.rights = issue.rights, i.date = issue.date, i.titles = issue.titles
  MERGE (s)-[:PUBLISHED_IN]->(i)

  // If journal_uid is provided, conditionally link SourceJournal
  FOREACH (_ IN CASE WHEN journal_uid IS NOT NULL THEN [1] ELSE [] END |
    MERGE (j:SourceJournal {uid: journal_uid})
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
