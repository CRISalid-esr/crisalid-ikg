MATCH (c:Concept {uri: $uri})
OPTIONAL MATCH (c)-[r:HAS_ALT_LABEL]->(:Literal {type: 'concept_alt_label'})
DELETE r
WITH DISTINCT c
FOREACH (al IN $alt_labels |
  MERGE (l:Literal {value:    trim(al.value),
                    language: coalesce(nullif(trim(al.language), ''), 'und'),
                    type:     'concept_alt_label'})
  MERGE (c)-[:HAS_ALT_LABEL]->(l)
)
