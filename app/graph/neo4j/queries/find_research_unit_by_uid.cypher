MATCH (s:ResearchUnit {uid: $research_unit_uid})
WITH s
MATCH (s)-[:HAS_IDENTIFIER]->(i:AgentIdentifier),
      (s)-[:HAS_NAME]->(n:Literal {type: 'research_unit_name'}),
      (s)-[:HAS_DESCRIPTION]->(d:Literal {type: 'research_unit_description'})
RETURN s, collect(DISTINCT n) AS names, collect(DISTINCT i) AS identifiers, collect(DISTINCT d) as descriptions