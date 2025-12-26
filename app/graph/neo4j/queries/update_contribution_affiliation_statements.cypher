MATCH (c:Contribution)
WHERE elementId(c) = $contribution_id
OPTIONAL MATCH (c)-[r:HAS_AFFILIATION_STATEMENT]->(:AuthorityOrganization)
DELETE r
WITH c
UNWIND $targets AS target_uid
MATCH (ao:AuthorityOrganization {uid: target_uid})
MERGE (c)-[:HAS_AFFILIATION_STATEMENT]->(ao);