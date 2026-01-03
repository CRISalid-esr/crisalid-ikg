MATCH (s:ResearchStructure {uid: $research_structure_uid})-[:HAS_NAME]->(l:Literal {type: 'research_structure_name'})
DETACH DELETE l