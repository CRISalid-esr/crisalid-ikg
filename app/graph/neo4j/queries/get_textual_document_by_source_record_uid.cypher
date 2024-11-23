MATCH (document:Document)-[:RECORDED_BY]->(s:SourceRecord {uid: $source_record_uid})
RETURN document