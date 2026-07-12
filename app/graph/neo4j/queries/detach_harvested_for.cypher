MATCH (:SourceRecord {uid: $source_record_uid})-[hf:HARVESTED_FOR]->(:Person {uid: $person_uid})
DELETE hf
