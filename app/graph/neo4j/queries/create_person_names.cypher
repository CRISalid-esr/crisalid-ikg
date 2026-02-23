MATCH (p:Person {uid: $person_uid})
UNWIND $names AS name
CREATE (pn:PersonName)

WITH p, pn, name
UNWIND name.first_names AS first_name
MERGE (fn:Literal {
  value:    trim(first_name.value),
  language: coalesce(nullif(trim(first_name.language), ''), 'und'),
  type:     'person_first_name'
})
MERGE (pn)-[:HAS_FIRST_NAME]->(fn)

WITH p, pn, name
UNWIND name.last_names AS last_name
MERGE (ln:Literal {
  value:    trim(last_name.value),
  language: coalesce(nullif(trim(last_name.language), ''), 'und'),
  type:     'person_last_name'
})
MERGE (pn)-[:HAS_LAST_NAME]->(ln)

MERGE (p)-[:HAS_NAME]->(pn);
