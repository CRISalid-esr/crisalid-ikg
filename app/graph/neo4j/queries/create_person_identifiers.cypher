MATCH (p:Person {id: $person_id})
UNWIND $identifiers AS identifier
MERGE (i:AgentIdentifier {type: identifier.type, value: identifier.value})
  ON CREATE SET i = identifier
  ON MATCH SET i = identifier
MERGE (p)-[:HAS_IDENTIFIER]->(i)