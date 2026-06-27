UNWIND $identifiers AS identifier
CALL {
  WITH identifier
  MATCH (p:Person)-[:HAS_IDENTIFIER]->(:AgentIdentifier {type: identifier.type, value: identifier.value})
  RETURN p
  UNION
  WITH identifier
  MATCH (p:Person)-[:RECORDED_BY]->(:SourcePerson)-[:HAS_IDENTIFIER]->(:SourcePersonIdentifier {type: identifier.type, value: identifier.value})
  RETURN p
}
RETURN DISTINCT
  identifier.type AS id_type,
  identifier.value AS id_value,
  p.uid AS person_uid,
  p.external AS external,
  p.display_name AS display_name
