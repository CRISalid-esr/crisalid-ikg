MATCH (document:Document)-[:RECORDED_BY]->(s:SourceRecord {uid: $source_record_uid})
WITH document
MATCH (document)-[:RECORDED_BY]->(s:SourceRecord)
WITH document, collect(s.uid) AS source_record_uids
RETURN document, source_record_uids