MATCH (p:Person)-[:HAS_IDENTIFIER]->(i1:AgentIdentifier {type: $identifier_type, value: $identifier_value})
OPTIONAL MATCH (p)-[:HAS_NAME]->(n:PersonName)
OPTIONAL MATCH (n)-[:HAS_FIRST_NAME]->(fn:Literal)
OPTIONAL MATCH (n)-[:HAS_LAST_NAME]->(ln:Literal)
MATCH (p)-[:HAS_IDENTIFIER]->(i2:AgentIdentifier)
WITH
  p,
  n,
  i2,
  fn,
  ln,
  collect(DISTINCT {value: fn.value, language: fn.language}) AS first_names,
  collect(DISTINCT {value: ln.value, language: ln.language}) AS last_names
WITH
  p,
  n,
  i2,
  collect(DISTINCT {
    name:        id(n),
    first_names: first_names,
    last_names:  last_names
  }) AS names
RETURN
  p,
  collect(DISTINCT i2) AS identifiers,
  names