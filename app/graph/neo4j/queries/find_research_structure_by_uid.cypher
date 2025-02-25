MATCH (s:ResearchStructure {uid: $research_structure_uid})
WITH s
MATCH (s)-[:HAS_IDENTIFIER]->(i:AgentIdentifier),
      (s)-[:HAS_NAME]->(n:Literal),
      (s)-[:HAS_DESCRIPTION]->(d:Literal)
RETURN s, collect(DISTINCT n) AS names, collect(DISTINCT i) AS identifiers, collect(DISTINCT d) as descriptions