MATCH (s:ResearchStructure {uid: $research_structure_uid})
UNWIND $identifiers AS identifier
MERGE (i:AgentIdentifier {type: identifier.type, value: identifier.value})
  ON CREATE SET i = identifier
  ON MATCH SET i = identifier
MERGE (s)-[:HAS_IDENTIFIER]->(i)