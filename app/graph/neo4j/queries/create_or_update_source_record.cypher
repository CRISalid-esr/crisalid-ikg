MERGE (s:SourceRecord {uid: $source_record_uid})
  ON CREATE SET s.harvester = $harvester, s.source_identifier = $source_identifier
  ON MATCH SET s.harvester = $harvester, s.source_identifier = $source_identifier

WITH s
OPTIONAL MATCH (s)-[r:HAS_TITLE]->()
DELETE r
FOREACH (title IN $titles |
  CREATE (t:Literal {value: title.value, language: title.language})
  CREATE (s)-[:HAS_TITLE]->(t)
)

WITH s
OPTIONAL MATCH (s)-[r:HAS_ABSTRACT]->()
DELETE r
FOREACH (abstract IN $abstracts |
  CREATE (a:Literal {value: abstract.value, language: abstract.language})
  CREATE (s)-[:HAS_ABSTRACT]->(a)
)

WITH s
OPTIONAL MATCH (s)-[r:HAS_IDENTIFIER]->()
DELETE r
FOREACH (identifier IN $identifiers |
  MERGE (i:PublicationIdentifier {type: identifier.type, value: identifier.value})
  MERGE (s)-[:HAS_IDENTIFIER]->(i)
)

WITH s
OPTIONAL MATCH (s)-[:PUBLISHED_IN]->(i:SourceIssue)-[r:ISSUED_BY]->(:SourceJournal)
DELETE r
FOREACH (_ IN CASE WHEN $issue IS NOT NULL THEN [1]
ELSE []
END |
MERGE (i:SourceIssue {source_identifier:$issue.source_identifier})
ON CREATE SET i.source = $issue.source, i.volume = $issue.volume, i.number = $issue.number, i.rights = $issue.rights, i.date = $issue.date, i.titles = $issue.titles
ON MATCH SET  i.source = $issue.source, i.volume = $issue.volume, i.number = $issue.number, i.rights = $issue.rights, i.date = $issue.date, i.titles = $issue.titles
MERGE (s)- [:PUBLISHED_IN] - >(i)

FOREACH (_ IN CASE WHEN $journal_uid IS NOT NULL THEN [1]
ELSE []
END |
MERGE (j:SourceJournal {uid:$journal_uid})
MERGE (i)- [:ISSUED_BY] - >(j)
)
)

WITH s, $person_uid AS person_uid
MATCH (p:Person {uid:person_uid})
MERGE (s)- [:HARVESTED_FOR] - >(p)
WITH s, $subject_uris AS subject_uris
OPTIONAL MATCH (s)- [r:HAS_SUBJECT] - >()
DELETE r

WITH s
OPTIONAL MATCH (s)- [r:HAS_SUBJECT] - >()
DELETE r

WITH s, $subject_uris AS subject_uris
UNWIND subject_uris AS subject_uri
MATCH (sub:Concept {uri:subject_uri})
MERGE (s)- [:HAS_SUBJECT] - >(sub)
