MATCH (p:Person {uid: $person_uid})-[r:EMPLOYED_AT]->(i:Institution)
DELETE r