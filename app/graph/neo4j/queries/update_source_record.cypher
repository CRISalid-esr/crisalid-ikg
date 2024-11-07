//v1.x Update source record
MERGE (s:SourceRecord {uid: $source_record_uid})
  ON MATCH SET s.harvester = $harvester, s.source_identifier = $source_identifier
WITH s
OPTIONAL MATCH (s)-[r:HAS_TITLE]->(existingTitle:Literal)
DELETE r, existingTitle
FOREACH (title IN $titles |
  MERGE (s)-[:HAS_TITLE]->(newTitle:Literal {value: title.value, language: title.language})
)


WITH s
OPTIONAL MATCH (s)-[r:HAS_ABSTRACT]->(existingAbstract:Literal)
DELETE r, existingAbstract
FOREACH (abstract IN $abstracts |
  MERGE (s)-[:HAS_ABSTRACT]->(newAbstract:Literal {value: abstract.value, language: abstract.language})
)
WITH s
OPTIONAL MATCH (s)-[r:HAS_IDENTIFIER]->(i:PublicationIdentifier)
DELETE r
WITH s, i
  WHERE NOT (i)--(:SourceRecord)
DELETE i
FOREACH (identifier IN $identifiers |
  MERGE (i:PublicationIdentifier {type: identifier.type, value: identifier.value})
  MERGE (s)-[:HAS_IDENTIFIER]->(i)
)
WITH s
OPTIONAL MATCH (s)-[p:PUBLISHED_IN]->(i:SourceIssue)
DELETE p
WITH s, i
  WHERE NOT (i)--(:SourceRecord)
DETACH DELETE i

FOREACH (_ IN CASE WHEN $issue IS NOT NULL THEN [1]
ELSE []
END |
MERGE (i:SourceIssue {source_identifier:$issue.source_identifier, source:$issue.source})
ON MATCH SET  i.volume = $issue.volume, i.number = $issue.number, i.rights = $issue.rights, i.date = $issue.date, i.titles = $issue.titles
ON CREATE SET i.volume = $issue.volume, i.number = $issue.number, i.rights = $issue.rights, i.date = $issue.date, i.titles = $issue.titles
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

WITH s
OPTIONAL MATCH (s)- [r:HAS_SUBJECT] - >(c:Concept)- [:HAS_PREF_LABEL|:HAS_ALT_LABEL] - >(l:Literal)
DELETE r
WITH s, c, l
WHERE NOT (c)- -(:SourceRecord)
DETACH DELETE c
WITH s, l
WHERE NOT (l)- -(:Concept)
DELETE l

//WITH s
//UNWIND $subject_uris AS subject_uri
//MATCH (sub:Concept {uri:subject_uri})
//MERGE (s)- [:HAS_SUBJECT] - >(sub)

with s
OPTIONAL MATCH (s)-[r:HAS_SUBJECT]->(existingSubject:Concept)
DELETE r
WITH s, existingSubject
FOREACH (subject_uri in $subject_uris|
  MERGE (sub:Concept{uri:subject_uri})
  MERGE(s)-[:HAS_SUBJECT]->(sub)
)