MATCH (p:Person {uid: $person_uid})
MATCH (s:ResearchStructure {uid: $structure_uid})
CREATE (p)-[:MEMBER_OF]->(s)