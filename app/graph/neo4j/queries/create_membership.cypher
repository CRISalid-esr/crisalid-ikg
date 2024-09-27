MATCH (p:Person {id: $person_id})
MATCH (s:ResearchStructure {id: $structure_id})
CREATE (p)-[:MEMBER_OF]->(s)