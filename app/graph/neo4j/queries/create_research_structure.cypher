CREATE (research_struct:Organisation:ResearchStructure {uid: $research_structure_uid})
WITH research_struct
FOREACH (name IN $names |
  CREATE (rs_name:Literal {value: name.value, language: name.language})
  CREATE (research_struct)-[:HAS_NAME]->(rs_name)
)
WITH research_struct
FOREACH (identifier IN $identifiers |
  CREATE (rs_identifier:AgentIdentifier {type:  identifier.type,
                                         value: identifier.value})
  CREATE (research_struct)-[:HAS_IDENTIFIER]->(rs_identifier)
)