MATCH (s:SourceRecord {uid: $source_record_uid})
DETACH DELETE s
