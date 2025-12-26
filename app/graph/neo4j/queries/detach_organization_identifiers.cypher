MATCH (o:Organisation {uid: $organization_uid})-[r:HAS_IDENTIFIER]->(i:AgentIdentifier)
WHERE NOT (i.type + ':' + i.value) IN $identifier_keys
DELETE r;
