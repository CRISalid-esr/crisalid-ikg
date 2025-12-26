MATCH (r:AuthorityOrganizationRoot {uid: $root_uid})
UNWIND $state_uids AS suid
MATCH (s:AuthorityOrganizationState {uid: suid})

OPTIONAL MATCH (other:AuthorityOrganizationRoot)-[rel:HAS_STATES]->(s)
WHERE other.uid <> $root_uid
DELETE rel

MERGE (r)-[:HAS_STATES]->(s);
