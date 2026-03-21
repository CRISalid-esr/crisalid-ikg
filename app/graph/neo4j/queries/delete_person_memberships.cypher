MATCH (p:Person {uid: $person_uid})-[r:MEMBER_OF]->(s:ResearchUnit)
DELETE r