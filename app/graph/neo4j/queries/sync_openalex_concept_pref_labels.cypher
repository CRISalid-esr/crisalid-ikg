MATCH (c:Concept {uri: $uri})
OPTIONAL MATCH (c)-[r:HAS_PREF_LABEL]->(:Literal {type: 'concept_pref_label'})
DELETE r
WITH DISTINCT c
FOREACH (pl IN $pref_labels |
  MERGE (l:Literal {value:    trim(pl.value),
                    language: coalesce(nullif(trim(pl.language), ''), 'und'),
                    type:     'concept_pref_label'})
  MERGE (c)-[:HAS_PREF_LABEL]->(l)
)
