MATCH (s:ResearchUnit {uid: $research_unit_uid})-[r:HAS_IDENTIFIER]->(i:AgentIdentifier)
  WHERE NOT (i.type IN $identifier_types AND i.value IN $identifier_values)
DELETE r;