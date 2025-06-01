MATCH (j:Journal)-[r:HAS_IDENTIFIER]->(i:JournalIdentifier)
  WHERE i.type = $identifier_type AND i.value = $identifier_value
RETURN j,
       collect(i) AS identifiers