MATCH (p:Person {uid: $person_uid})
UNWIND $identifiers AS identifier
MERGE (i:AgentIdentifier {type: identifier.type, value: identifier.value})
  ON CREATE SET i = identifier
  ON MATCH SET i = identifier
MERGE (p)-[:HAS_IDENTIFIER]->(i)