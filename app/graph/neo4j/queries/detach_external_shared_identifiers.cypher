// Detach, from external persons, every HAS_IDENTIFIER edge whose AgentIdentifier is also owned
// by an internal person, restoring one-owner-per-identifier. The AgentIdentifier node and the
// external Person are left intact.
MATCH (ext:Person {external: true})-[r:HAS_IDENTIFIER]->(ai:AgentIdentifier)
WHERE EXISTS {
  MATCH (:Person {external: false})-[:HAS_IDENTIFIER]->(ai)
}
WITH DISTINCT r
DELETE r
RETURN count(r) AS detached
