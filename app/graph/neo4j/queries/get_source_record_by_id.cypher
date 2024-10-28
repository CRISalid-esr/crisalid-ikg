MATCH (s:SourceRecord {uid: $source_record_uid})
OPTIONAL MATCH (s)-[:HAS_TITLE]->(t:Literal)
OPTIONAL MATCH (s)-[:HAS_ABSTRACT]->(a:Literal)
OPTIONAL MATCH (s)-[:HAS_IDENTIFIER]->(i:PublicationIdentifier)
OPTIONAL MATCH (s)-[:HARVESTED_FOR]->(p:Person)
OPTIONAL MATCH (s)-[:HAS_SUBJECT]->(c:Concept)
RETURN s,
       collect(DISTINCT t) AS titles,
       collect(DISTINCT i) AS identifiers,
       collect(DISTINCT a) AS abstracts,
       collect(DISTINCT p) AS persons,
       collect(DISTINCT c) AS subjects


