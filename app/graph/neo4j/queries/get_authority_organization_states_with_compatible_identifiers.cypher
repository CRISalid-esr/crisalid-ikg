UNWIND $identifiers AS qid

MATCH (o:AuthorityOrganizationState)-[:HAS_IDENTIFIER]->(
  i:AgentIdentifier {type: qid.type, value: qid.value}
)
WITH DISTINCT o, $identifiers AS wanted

WHERE NOT EXISTS {
  UNWIND wanted AS w
  MATCH (o)-[:HAS_IDENTIFIER]->(ci:AgentIdentifier {type: w.type})
  WHERE ci.value <> w.value
}

OPTIONAL MATCH (o)-[:HAS_NAME]->(n:Literal {type: 'authority_organization_state_name'})
OPTIONAL MATCH (o)-[:HAS_IDENTIFIER]->(allI:AgentIdentifier)

RETURN
  o,
  collect(DISTINCT n) AS names,
  collect(DISTINCT allI {type: allI.type, value: allI.value}) AS identifiers;
