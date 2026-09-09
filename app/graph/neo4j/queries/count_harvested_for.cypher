MATCH (:SourceRecord {uid: $source_record_uid})-[r:HARVESTED_FOR]->(:Person)
RETURN count(r) AS harvested_for_count
