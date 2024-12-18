MATCH (s:SourceRecord {uid: $source_record_uid})
MATCH (c:SourcePerson {uid: $contributor_uid})
CREATE (sc:SourceContribution {rank: $rank})
SET sc.role = $role
MERGE (s)-[:HAS_CONTRIBUTION]->(sc)
MERGE (sc)-[:CONTRIBUTOR]->(c)
WITH sc
UNWIND $affiliation_uids AS affiliation_uid
MATCH (o:SourceOrganization {uid: affiliation_uid})
MERGE (sc)-[:HAS_AFFILIATION]->(o)