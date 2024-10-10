CREATE (p:Person {uid: $person_uid})
WITH p
FOREACH (name IN $names |
  CREATE (pn:PersonName)
  CREATE (p)-[:HAS_NAME]->(pn)
  FOREACH (first_name IN name.first_names |
    CREATE (fn:Literal {value: first_name.value, language: first_name.language})
    CREATE (pn)-[:HAS_FIRST_NAME]->(fn)
  )
  FOREACH (last_name IN name.last_names |
    CREATE (ln:Literal {value: last_name.value, language: last_name.language})
    CREATE (pn)-[:HAS_LAST_NAME]->(ln)
  )
)
WITH p
UNWIND $identifiers AS identifier
CREATE (i:AgentIdentifier {type: identifier.type, value: identifier.value})
CREATE (p)-[:HAS_IDENTIFIER]->(i)