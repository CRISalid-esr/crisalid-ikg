MATCH (s:Institution {uid: $institution_uid})
MATCH (s)-[:HAS_IDENTIFIER]->(id:AgentIdentifier),
      (s)-[:HAS_NAME]->(n:Literal)
RETURN s, collect(DISTINCT n) AS names, collect(DISTINCT id) AS identifiers
