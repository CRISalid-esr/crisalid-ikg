MERGE (doc:Document:TextualDocument {uid: $document_uid})
  ON CREATE SET doc.to_be_recomputed = $to_be_recomputed,
                doc.to_be_deleted = $to_be_deleted
  ON MATCH SET doc.to_be_recomputed = $to_be_recomputed,
               doc.to_be_deleted = $to_be_deleted
WITH doc
OPTIONAL MATCH (doc_to_merge_into:Document:TextualDocument {uid: $to_be_merged_into_uid})
FOREACH (_ IN CASE WHEN doc_to_merge_into IS NOT NULL THEN [1] ELSE [] END |
  MERGE (doc)-[:TO_BE_MERGED_INTO]->(doc_to_merge_into)
)
WITH doc
OPTIONAL MATCH (doc)-[r:RECORDED_BY]->(s:SourceRecord)
  WHERE NOT s.uid IN $source_record_uids
DELETE r
WITH doc
UNWIND $source_record_uids AS uid
OPTIONAL MATCH (sr:SourceRecord {uid: uid})
MERGE (doc)-[:RECORDED_BY]->(sr)
WITH doc
RETURN doc
