MATCH (p:Person {uid: $person_uid})-[r:HAS_IDENTIFIER]->(i:AgentIdentifier {type: $identifier_type, value: $identifier_value})
DELETE r
WITH i
OPTIONAL MATCH (other:Person)-[:HAS_IDENTIFIER]->(i)
WITH i, count(other) AS remaining_owners
FOREACH (_ IN CASE WHEN remaining_owners = 0 THEN [1] ELSE [] END |
  DETACH DELETE i
)
RETURN remaining_owners
