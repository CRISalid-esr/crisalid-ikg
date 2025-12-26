MATCH (o:AuthorityOrganizationState {uid: $uid})
FOREACH (name IN $names |
  CREATE (n:Literal {value: name.value, language: name.language})
  CREATE (o)-[:HAS_NAME]->(n)
);
