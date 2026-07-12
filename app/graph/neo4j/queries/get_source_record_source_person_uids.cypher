MATCH (:SourceRecord {uid: $source_record_uid})-[:HAS_CONTRIBUTION]->(:SourceContribution)-[:CONTRIBUTOR]->(sp:SourcePerson)
RETURN collect(DISTINCT sp.uid) AS source_person_uids
