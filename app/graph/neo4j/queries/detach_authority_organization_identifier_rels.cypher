MATCH (o:AuthorityOrganizationState {uid: $uid})-[r:HAS_IDENTIFIER]->(i:AgentIdentifier)
WHERE NOT (i.type + ':' + i.value) IN $identifier_keys
DELETE r;
