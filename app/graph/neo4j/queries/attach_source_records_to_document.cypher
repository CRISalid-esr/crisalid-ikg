MATCH (doc:Document:Document {uid: $document_uid})
SET doc.to_be_recomputed = true
WITH doc
UNWIND $source_record_uids AS uid
MATCH (sr:SourceRecord {uid: uid})
MERGE (doc)-[:RECORDED_BY]->(sr)
WITH doc
RETURN doc
