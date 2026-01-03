CREATE (s:SourceRecord {
    uid: $source_record_uid,
    url: $source_record_url,
    harvester: $harvester,
    source_identifier: $source_identifier,
    document_types: $document_types,
    issued: CASE WHEN $issued IS NOT NULL THEN datetime($issued) ELSE NULL END,
    raw_issued: $raw_issued,
    hal_collection_codes: $hal_collection_codes,
    hal_submit_type: $hal_submit_type
})

WITH s
FOREACH (title IN $titles |
  MERGE (t:Literal {
    value: trim(title.value),
    language: coalesce(nullif(trim(title.language), ''), 'und'),
    type: "source_record_title"
  })
  MERGE (s)-[:HAS_TITLE]->(t)
)
FOREACH (abstract IN $abstracts |
  MERGE (a:Literal {
    value: trim(abstract.value),
    language: coalesce(nullif(trim(abstract.language), ''), 'und'),
    type: "source_record_abstract"
  })
  MERGE (s)-[:HAS_ABSTRACT]->(a)
)
FOREACH (identifier IN $identifiers |
  MERGE (i:PublicationIdentifier {type: identifier.type, value: identifier.value})
  MERGE (s)-[:HAS_IDENTIFIER]->(i)
)

WITH s
FOREACH (_ IN CASE WHEN $issue IS NOT NULL THEN [1] ELSE [] END |
  MERGE (i:SourceIssue {source_identifier: $issue.source_identifier, source: $issue.source})
  ON CREATE SET i.volume = $issue.volume, i.number = $issue.number, i.rights = $issue.rights, i.date = $issue.date, i.titles = $issue.titles
  ON MATCH SET  i.volume = $issue.volume, i.number = $issue.number, i.rights = $issue.rights, i.date = $issue.date, i.titles = $issue.titles
  MERGE (s)-[:PUBLISHED_IN]->(i)

  FOREACH (_ IN CASE WHEN $journal_uid IS NOT NULL THEN [1] ELSE [] END |
    MERGE (j:SourceJournal {uid: $journal_uid})
    MERGE (i)-[:ISSUED_BY]->(j)
  )
)
WITH s, $person_uid AS person_uid
MATCH (p:Person {uid: person_uid})
MERGE (s)-[:HARVESTED_FOR]->(p)

WITH s, $subject_uids AS subject_uids
UNWIND subject_uids AS subject_uid
MATCH (sub:Concept {uid: subject_uid})
MERGE (s)-[:HAS_SUBJECT]->(sub)
