MATCH (p:Person {id: $person_id})
OPTIONAL MATCH (p)-[:HAS_NAME]->(pn:PersonName)
OPTIONAL MATCH (pn)-[:HAS_FIRST_NAME]->(fn:Literal)
OPTIONAL MATCH (pn)-[:HAS_LAST_NAME]->(ln:Literal)
MATCH (p)-[:HAS_IDENTIFIER]->(i:AgentIdentifier)
WITH
  p,
  pn,
  i,
  fn,
  ln,
  collect(DISTINCT {value: fn.value, language: fn.language}) AS first_names,
  collect(DISTINCT {value: ln.value, language: ln.language}) AS last_names
WITH
  p,
  pn,
  i,
  collect(DISTINCT {
    name:        id(pn),
    first_names: first_names,
    last_names:  last_names
  }) AS names
RETURN
  p,
  collect(DISTINCT i) AS identifiers,
  names