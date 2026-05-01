MATCH (s:SourceRecord)-[r:HARVESTED_FOR]->(p:Person {uid: $person_uid})
WHERE r.identifier_used_type = $identifier_used_type
  AND r.identifier_used_value = $identifier_used_value
RETURN collect(s.uid) AS source_record_uids
