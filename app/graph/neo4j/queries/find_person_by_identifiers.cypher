UNWIND $identifiers AS identifier
MATCH (p:Person)-[:HAS_IDENTIFIER]->(id:AgentIdentifier)
WHERE id.type = identifier.type AND id.value = identifier.value
RETURN DISTINCT p.uid AS uid
LIMIT 1