MATCH (s:ResearchStructure {uid: $research_structure_uid})
UNWIND $names AS name
MERGE (l:Literal {
  value:    trim(name.value),
  language: coalesce(nullif(trim(name.language), ''), 'und'),
  type:     'research_structure_name'
})
MERGE (s)-[:HAS_NAME]->(l);
