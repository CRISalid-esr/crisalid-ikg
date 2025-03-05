MATCH (s)-[:HAS_IDENTIFIER]->(i:AgentIdentifier)
WHERE ANY(identifier IN $identifiers WHERE i.type = identifier.type AND i.value = identifier.value)
WITH DISTINCT s
MATCH (s)-[:HAS_IDENTIFIER]->(id:AgentIdentifier),
      (s)-[:HAS_NAME]->(n:Literal)
RETURN s, collect(DISTINCT n) AS names, collect(DISTINCT id) AS identifiers
