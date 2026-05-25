MATCH (s:SourceRecord {uid: $source_record_uid})

OPTIONAL MATCH (s)-[r:HAS_TOPIC]->()
DELETE r

WITH DISTINCT s
UNWIND $topics AS t
MATCH (topic:Concept:Topic {uri: t.uri})
MERGE (s)-[rel:HAS_TOPIC]->(topic)
SET rel.score = t.score
