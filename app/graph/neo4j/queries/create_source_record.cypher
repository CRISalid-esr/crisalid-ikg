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
WITH s, $person_uid AS person_uid
MATCH (p:Person {uid: person_uid})
MERGE (s)-[:HARVESTED_FOR]->(p)
WITH s, $subject_uris AS subject_uris
UNWIND subject_uris AS subject_uri
MATCH (sub:Concept {uri: subject_uri})
MERGE (s)-[:HAS_SUBJECT]->(sub)