MATCH (o:AuthorityOrganizationState {uid: $uid})-[:HAS_NAME]->(n:Literal)
DETACH DELETE n;
