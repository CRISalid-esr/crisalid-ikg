MATCH (s)-[:HAS_IDENTIFIER]->(:AgentIdentifier {type: $identifier_type, value: $identifier_value})
WITH s
MATCH (s)-[:HAS_IDENTIFIER]->(i:AgentIdentifier),
      (s)-[:HAS_NAME]->(n:Literal)
RETURN s, collect(DISTINCT n) AS names, collect(DISTINCT i) AS identifiers