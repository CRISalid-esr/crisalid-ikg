// create an :INFERRED_EQUIVALENT relationship (if not present) between all source records in source_record_uids, no matter the direction
MATCH (source_record:SourceRecord)
WHERE source_record.uid IN $source_record_uids
WITH source_record
MATCH (target_source_record:SourceRecord)
WHERE target_source_record.uid IN $source_record_uids
AND source_record <> target_source_record
WITH source_record, target_source_record
//avoid unnecessary bidirectional relationships
WHERE source_record.uid < target_source_record.uid
MERGE (source_record)-[:INFERRED_EQUIVALENT]->(target_source_record)