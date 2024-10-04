CREATE (s:SourceRecord {uid: $source_record_uid, harvester: $harvester, source_identifier: $source_identifier})
WITH s
UNWIND $titles AS title
CREATE (t:Literal {value: title.value, language: title.language})
CREATE (s)-[:HAS_TITLE]->(t)
WITH s
UNWIND $abstracts AS abstract
CREATE (a:Literal {value: abstract.value, language: abstract.language})
CREATE (s)-[:HAS_ABSTRACT]->(a)
WITH s
UNWIND $identifiers AS identifier
CREATE (i:PublicationIdentifier {type: identifier.type, value: identifier.value})
CREATE (s)-[:HAS_IDENTIFIER]->(i)
WITH s, $person_uid AS person_uid
MATCH (p:Person {uid: person_uid})
MERGE (s)-[:HARVESTED_FOR]->(p)