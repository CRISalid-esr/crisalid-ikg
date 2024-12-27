MATCH (doc:TextualDocument {uid: $textual_document_uid})
MATCH (doc)-[:RECORDED_BY]->(s:SourceRecord)
RETURN collect(DISTINCT s.uid) AS source_record_uids


