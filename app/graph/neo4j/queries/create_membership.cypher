MATCH (p:Person {uid: $person_uid})
MATCH (s:ResearchUnit {uid: $structure_uid})
CREATE (p)-[:MEMBER_OF]->(s)