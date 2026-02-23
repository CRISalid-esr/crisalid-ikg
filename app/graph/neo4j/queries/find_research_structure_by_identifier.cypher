MATCH (s)-[:HAS_IDENTIFIER]->(:AgentIdentifier {type: $identifier_type, value: $identifier_value})
WITH s
MATCH (s)-[:HAS_IDENTIFIER]->(i:AgentIdentifier),
      (s)-[:HAS_NAME]->(n:Literal {type: 'research_structure_name'}),
      (s)-[:HAS_DESCRIPTION]->(d:Literal {type: 'research_structure_description'})
RETURN s, collect(DISTINCT n) AS names, collect(DISTINCT i) AS identifiers, collect(DISTINCT d) as descriptions