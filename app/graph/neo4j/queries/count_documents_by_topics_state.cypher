MATCH (doc:Document)
RETURN count(doc) AS total,
       count(doc.topics_input_hash) AS computed,
       count { (doc)-[:HAS_TOPIC {source: 'crisalid'}]->() } AS crisalid_edges,
       count { (doc)-[:HAS_TOPIC {source: 'openalex'}]->() } AS openalex_edges
