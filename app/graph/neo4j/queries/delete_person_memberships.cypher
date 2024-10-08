MATCH (p:Person {uid: $person_uid})-[r:MEMBER_OF]->(s:ResearchStructure)
DELETE r