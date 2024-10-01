MATCH (s:SourceRecord {id: $source_record_id})
OPTIONAL MATCH (s)-[:HAS_TITLE]->(t:Literal)
OPTIONAL MATCH (s)-[:HAS_ABSTRACT]->(a:Literal)
OPTIONAL MATCH (s)-[:HAS_IDENTIFIER]->(i:PublicationIdentifier)
OPTIONAL MATCH (s)-[:HARVESTED_FOR]->(p:Person)
RETURN s,
       collect(t) AS titles,
       collect(i) AS identifiers,
       collect(a) AS abstracts,
       collect(p) AS persons

