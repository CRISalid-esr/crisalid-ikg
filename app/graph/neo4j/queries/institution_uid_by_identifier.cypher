MATCH (i:Institution)-[:HAS_IDENTIFIER]->(:AgentIdentifier {type: $identifier_type, value: $identifier_value})
RETURN i.uid AS uid
ORDER BY coalesce(i.external, false), i.uid
LIMIT 1
