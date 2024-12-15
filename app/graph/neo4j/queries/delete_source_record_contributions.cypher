MATCH (:SourceRecord {uid: $person_uid})-[:HAS_CONTRIBUTION]->(c:SourceContribution)
DETACH DELETE c