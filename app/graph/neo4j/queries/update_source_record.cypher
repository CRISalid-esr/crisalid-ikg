MERGE (s:SourceRecord {uid: $source_record_uid})
  ON MATCH SET
  s.url = $source_record_url,
  s.harvester = $harvester,
  s.source_identifier = $source_identifier,
  s.document_types = $document_types,
  s.issued = CASE WHEN $issued IS NOT NULL THEN datetime($issued)
    ELSE null
    END,
  s.raw_issued = $raw_issued,
  s.hal_collection_codes = $hal_collection_codes,
  s.hal_submit_type = $hal_submit_type

WITH s
OPTIONAL MATCH (s)-[r:HAS_TITLE]->(:Literal {type: 'source_record_title'})
DELETE r
WITH DISTINCT s
FOREACH (title IN $titles |
  MERGE (t:Literal {
    value:    trim(title.value),
    language: coalesce(nullif(trim(title.language), ''), 'und'),
    type:     'source_record_title'
  })
  MERGE (s)-[:HAS_TITLE]->(t)
)

WITH s
OPTIONAL MATCH (s)-[r:HAS_ABSTRACT]->(:TextLiteral {type: 'source_record_abstract'})
DELETE r
WITH DISTINCT s
FOREACH (abstract IN $abstracts |
  MERGE (a:TextLiteral {key: abstract.key, type: 'source_record_abstract'})
    ON CREATE SET
    a.value = abstract.value,
    a.language = coalesce(nullif(trim(abstract.language), ''), 'und'),
    a.type = 'source_record_abstract'
  MERGE (s)-[:HAS_ABSTRACT]->(a)
)

WITH s
OPTIONAL MATCH (s)-[r:HAS_IDENTIFIER]->(:PublicationIdentifier)
DELETE r
WITH DISTINCT s
FOREACH (identifier IN $identifiers |
  MERGE (i:PublicationIdentifier {type: identifier.type, value: identifier.value})
  MERGE (s)-[:HAS_IDENTIFIER]->(i)
)


WITH s
OPTIONAL MATCH (s)-[p:PUBLISHED_IN]->(i:SourceIssue)
DELETE p

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
MERGE (s)- [r:HARVESTED_FOR] - >(p)
ON MATCH SET r.identifier_used_type = $identifier_used_type, r.identifier_used_value = $identifier_used_value
ON CREATE SET r.identifier_used_type = $identifier_used_type, r.identifier_used_value = $identifier_used_value

WITH DISTINCT s
OPTIONAL MATCH (s)- [r:HAS_SUBJECT] - >(c:Concept)
WHERE NOT c.uid IN $subject_uids
DELETE r

WITH DISTINCT s
UNWIND $subject_uids AS subject_uid
MATCH (c:Concept {uid:subject_uid})
MERGE (s)- [:HAS_SUBJECT] - >(c)