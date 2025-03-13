MERGE (i:Organisation:Institution {uid: $uid})
  ON CREATE SET i.uid = $uid

WITH i

FOREACH (id_data IN CASE WHEN size($identifiers) > 0 THEN $identifiers
  ELSE []
  END |
  MERGE (id:AgentIdentifier {type: id_data.type, value: id_data.value})
  MERGE (i)-[:HAS_IDENTIFIER]->(id)
)

RETURN i
