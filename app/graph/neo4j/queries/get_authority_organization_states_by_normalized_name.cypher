MATCH (o:AuthorityOrganizationState {normalized_name: $normalized_name})

OPTIONAL MATCH (o)-[:HAS_NAME]->(n:Literal {type: 'authority_organization_state_name'})
OPTIONAL MATCH (o)-[:HAS_IDENTIFIER]->(i:AgentIdentifier)

RETURN
  o AS o,
  collect(DISTINCT n) AS names,
  collect(DISTINCT i {type: i.type, value: i.value}) AS identifiers;
