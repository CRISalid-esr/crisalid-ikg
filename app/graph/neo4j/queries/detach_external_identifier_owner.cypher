MATCH (ext:Person {external: true})-[r:HAS_IDENTIFIER]->(ai:AgentIdentifier {type: $identifier_type, value: $identifier_value})
WHERE EXISTS {
  MATCH (:Person {external: false})-[:HAS_IDENTIFIER]->(ai)
}
DELETE r
RETURN count(r) AS detached
