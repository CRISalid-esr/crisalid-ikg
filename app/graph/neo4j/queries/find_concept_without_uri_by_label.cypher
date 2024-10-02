MATCH (c:Concept)-[:HAS_PREF_LABEL]->(pl:Literal {value: $label})
  WHERE NOT exists(c.uri)
RETURN c