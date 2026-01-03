MATCH (p:Person {uid: $person_uid})-[:HAS_NAME]->(n:PersonName)
DETACH DELETE n;