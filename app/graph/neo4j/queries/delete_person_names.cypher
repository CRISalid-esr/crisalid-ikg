MATCH (p:Person {uid: $person_uid})-[:HAS_NAME]->(n:PersonName)
MATCH (n)-[:HAS_FIRST_NAME]->(fn:Literal {type: 'person_first_name'})
MATCH (n)-[:HAS_LAST_NAME]->(ln:Literal {type: 'person_last_name'})
DETACH DELETE n, fn, ln