MATCH (s:SourceRecord {uid: $source_record_uid})
MATCH (c:SourcePerson {uid: $contributor_uid})
CREATE (sc:SourceContribution {rank: $rank})
SET sc.role = $role
MERGE (s)-[:HAS_CONTRIBUTION]->(sc)
MERGE (sc)-[:CONTRIBUTOR]->(c)