MERGE (s:SourceRecord {uid: $source_record_uid})
  ON MATCH SET
    s.url = $source_record_url,
    s.harvester = $harvester,
    s.source_identifier = $source_identifier,
    s.document_types = $document_types,
    s.issued = CASE WHEN $issued IS NOT NULL THEN datetime($issued) ELSE NULL END,
    s.raw_issued = $raw_issued,
    s.hal_collection_codes = $hal_collection_codes,
    s.hal_submit_type = $hal_submit_type

WITH s
OPTIONAL MATCH (s)-[r:HAS_TITLE]->(t:Literal)
DELETE r, t
WITH DISTINCT s
FOREACH (title IN $titles |
  CREATE (s)-[:HAS_TITLE]->(t:Literal {value: title.value, language: title.language})
)

WITH s
OPTIONAL MATCH (s)-[r:HAS_ABSTRACT]->(a:Literal)
DELETE r, a
WITH DISTINCT s
FOREACH (abstract IN $abstracts |
  CREATE (s)-[:HAS_ABSTRACT]->(a:Literal {value: abstract.value, language: abstract.language})
)

WITH s
OPTIONAL MATCH (s)-[r:HAS_IDENTIFIER]->(:PublicationIdentifier)
DELETE r
WITH DISTINCT s
FOREACH (identifier IN $identifiers |
  MERGE (i:PublicationIdentifier {type: identifier.type, value: identifier.value})
  CREATE (s)-[:HAS_IDENTIFIER]->(i)
)

WITH s
OPTIONAL MATCH (s)-[p:PUBLISHED_IN]->(i:SourceIssue)
DELETE p
WITH s, i
  WHERE NOT (i)--(:SourceRecord)
DETACH DELETE i

WITH DISTINCT s
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

WITH DISTINCT s
MATCH (p:Person {uid:$person_uid})
MERGE (s)- [:HARVESTED_FOR] - >(p)

WITH DISTINCT s
OPTIONAL MATCH (s)- [r:HAS_SUBJECT] - >(c:Concept)
WHERE NOT c.uid IN $subject_uids
OPTIONAL MATCH (c)- [:HAS_PREF_LABEL|:HAS_ALT_LABEL] - >(l:Literal)
DELETE r

WITH DISTINCT s
UNWIND $subject_uids AS subject_uid
MATCH (c:Concept {uid:subject_uid})
MERGE (s)- [:HAS_SUBJECT] - >(c)