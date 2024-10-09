MATCH (s:ResearchStructure {uid: $research_structure_uid})
UNWIND $names AS name
CREATE (l:Literal {value: name.value, language: name.language})
CREATE (s)-[:HAS_NAME]->(l)