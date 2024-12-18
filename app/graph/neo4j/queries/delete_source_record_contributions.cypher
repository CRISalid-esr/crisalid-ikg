MATCH (:SourceRecord {uid: $source_record_uid})-[:HAS_CONTRIBUTION]->(c:SourceContribution)
DETACH DELETE c