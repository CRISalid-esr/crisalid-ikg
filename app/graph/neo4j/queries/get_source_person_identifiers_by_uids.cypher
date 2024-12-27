UNWIND $uids AS uid
MATCH (sp:SourcePerson {uid: uid})-[:HAS_IDENTIFIER]->(identifier:SourcePersonIdentifier)
RETURN DISTINCT identifier.type AS type, identifier.value AS value
