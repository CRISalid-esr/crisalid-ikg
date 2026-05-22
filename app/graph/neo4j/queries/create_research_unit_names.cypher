MATCH (s:ResearchUnit {uid: $research_unit_uid})
UNWIND $names AS name
MERGE (l:Literal:Embeddable {
  value:    trim(name.value),
  language: coalesce(nullif(trim(name.language), ''), 'und'),
  type:     'research_unit_name'
})
ON CREATE SET l.embedding_status = 'pending'
MERGE (s)-[:HAS_NAME]->(l);
