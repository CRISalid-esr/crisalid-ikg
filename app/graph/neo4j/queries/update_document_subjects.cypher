MATCH (doc:Document:Document {uid: $document_uid})
OPTIONAL MATCH (doc)-[r:HAS_SUBJECT]->(c:Concept)
WHERE NOT c.uid IN $subject_uids
DELETE r

WITH DISTINCT doc
OPTIONAL MATCH (c:Concept) WHERE c.uid IN $subject_uids  // Get only existing Concept nodes
WITH DISTINCT doc, collect(c) AS existing_concepts
FOREACH (c IN existing_concepts |
  MERGE (doc)-[:HAS_SUBJECT]->(c)
)