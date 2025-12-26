MATCH (o:AuthorityOrganizationState {uid: $state_uid})

OPTIONAL MATCH (o)-[:HAS_NAME]->(n:Literal)
OPTIONAL MATCH (o)-[:HAS_IDENTIFIER]->(i:AgentIdentifier)

RETURN
  o AS o,
  collect(DISTINCT n) AS names,
  collect(DISTINCT i {type:i.type, value:i.value}) AS identifiers;
