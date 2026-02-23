MATCH (doc:Document {uid: $document_uid})
MATCH (doc)-[:RECORDED_BY]->(s:SourceRecord)
RETURN collect(DISTINCT s.uid) AS source_record_uids


