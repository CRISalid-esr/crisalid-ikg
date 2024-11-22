// Delete all INFERRED_EQUIVALENT relationships between a source record and a list of target source records
MATCH (source_record:SourceRecord {uid: $source_record_uid}) -[r:INFERRED_EQUIVALENT]- (target_source_record:SourceRecord)
WHERE target_source_record.uid IN $target_source_record_uids
DELETE r