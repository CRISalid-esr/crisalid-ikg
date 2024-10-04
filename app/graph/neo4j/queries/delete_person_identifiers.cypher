MATCH (p:Person {uid: $person_uid})-[:HAS_IDENTIFIER]->(i:AgentIdentifier)
  WHERE NOT (i.type IN $identifier_types AND i.value IN $identifier_values)
DETACH DELETE i