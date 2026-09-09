MATCH (o:AuthorityOrganizationState {uid: $uid})
FOREACH (name IN $names |
  MERGE (n:Literal:Embeddable {
    value:    trim(name.value),
    language: coalesce(nullif(trim(name.language), ''), 'und'),
    type:     'authority_organization_state_name'
  })
  ON CREATE SET n.embedding_status = 'pending'
  MERGE (o)-[:HAS_NAME]->(n)
);