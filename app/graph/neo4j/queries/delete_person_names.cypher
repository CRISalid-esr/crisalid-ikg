MATCH (p:Person {uid: $person_uid})-[:HAS_NAME]->(n:PersonName)
MATCH (n)-[:HAS_FIRST_NAME]->(fn:Literal)
MATCH (n)-[:HAS_LAST_NAME]->(ln:Literal)
DETACH DELETE n, fn, ln