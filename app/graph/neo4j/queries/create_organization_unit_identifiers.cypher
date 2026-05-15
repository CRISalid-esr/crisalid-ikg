MATCH (o:OrganizationUnit {uid: $uid})
FOREACH (i IN $identifiers |
  MERGE (ai:AgentIdentifier {type: i.type, value: i.value})
  MERGE (o)-[:HAS_IDENTIFIER]->(ai)
)
