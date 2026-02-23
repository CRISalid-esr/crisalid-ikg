MATCH (o:AuthorityOrganizationState {uid: $uid})
FOREACH (name IN $names |
  MERGE (n:Literal {
    value:    trim(name.value),
    language: coalesce(nullif(trim(name.language), ''), 'und'),
    type:     'authority_organization_state_name'
  })
  MERGE (o)-[:HAS_NAME]->(n)
);