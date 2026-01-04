MATCH (s:ResearchStructure {uid: $research_structure_uid})-[r:HAS_IDENTIFIER]->(i:AgentIdentifier)
  WHERE NOT (i.type IN $identifier_types AND i.value IN $identifier_values)
DELETE r;