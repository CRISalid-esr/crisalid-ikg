MATCH (s:ResearchStructure {uid: $research_structure_uid})-[:HAS_NAME]->(l:Literal)
DETACH DELETE l