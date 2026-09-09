MATCH (doc:Document {uid: $document_uid})
OPTIONAL MATCH (doc)-[old:HAS_TOPIC {source: 'openalex'}]->()
DELETE old
WITH DISTINCT doc
OPTIONAL MATCH (doc)-[:RECORDED_BY]->(:SourceRecord)-[r:HAS_TOPIC]->(topic:Concept:Topic)
WITH doc, topic, max(r.score) AS score
WHERE topic IS NOT NULL
MERGE (doc)-[rel:HAS_TOPIC {source: 'openalex'}]->(topic)
SET rel.score = score
