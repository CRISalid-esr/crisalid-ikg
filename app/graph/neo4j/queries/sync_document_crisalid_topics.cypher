MATCH (doc:Document {uid: $document_uid})
OPTIONAL MATCH (doc)-[old:HAS_TOPIC {source: 'crisalid'}]->(old_topic:Concept)
WITH doc, collect(DISTINCT old_topic.uid) AS previous_uids, collect(old) AS old_rels
FOREACH (old IN old_rels | DELETE old)
SET doc.topics_input_hash = $input_hash,
    doc.topics_model = $model,
    doc.topics_computed_at = datetime()
WITH doc, previous_uids
UNWIND CASE WHEN size($topics) = 0 THEN [null] ELSE $topics END AS t
OPTIONAL MATCH (topic:Concept:Topic {uid: t.uid})
FOREACH (_ IN CASE WHEN topic IS NULL THEN [] ELSE [1] END |
  MERGE (doc)-[rel:HAS_TOPIC {source: 'crisalid'}]->(topic)
  SET rel.score = t.score, rel.model = $model, rel.computed_at = datetime()
)
WITH doc, previous_uids, collect(topic.uid) AS linked_uids
RETURN doc.uid AS document_uid, previous_uids, linked_uids
