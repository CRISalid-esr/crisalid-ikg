CREATE (p:Person {id: $person_id})
WITH p
UNWIND $names AS name
CREATE (pn:PersonName)
WITH p, pn, name
UNWIND name.first_names AS first_name
CREATE (fn:Literal {value: first_name.value, language: first_name.language})
CREATE (pn)-[:HAS_FIRST_NAME]->(fn)
WITH p, pn, name
UNWIND name.last_names AS last_name
CREATE (ln:Literal {value: last_name.value, language: last_name.language})
CREATE (pn)-[:HAS_LAST_NAME]->(ln)
CREATE (p)-[:HAS_NAME]->(pn)
WITH p
UNWIND $identifiers AS identifier
CREATE (i:AgentIdentifier {type: identifier.type, value: identifier.value})
CREATE (p)-[:HAS_IDENTIFIER]->(i)