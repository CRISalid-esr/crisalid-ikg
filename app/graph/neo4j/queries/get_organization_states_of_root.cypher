MATCH (r:AuthorityOrganizationRoot {uid: $root_uid})-[:HAS_STATES]->(s:AuthorityOrganizationState)
RETURN collect(DISTINCT s.uid) AS state_uids;
