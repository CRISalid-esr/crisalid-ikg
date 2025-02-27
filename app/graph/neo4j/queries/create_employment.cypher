MATCH (p:Person {uid: $person_uid})
MATCH (i:Institution {uid: $institution_uid})
CREATE (p)-[:EMPLOYED_AT {position_code: $position}]->(i)
RETURN p, i