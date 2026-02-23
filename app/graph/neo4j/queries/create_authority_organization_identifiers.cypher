MATCH (o:AuthorityOrganizationState {uid: $uid})
FOREACH (identifier IN $identifiers |
  MERGE (i:AgentIdentifier {type: identifier.type, value: identifier.value})
  MERGE (o)-[:HAS_IDENTIFIER]->(i)
);
