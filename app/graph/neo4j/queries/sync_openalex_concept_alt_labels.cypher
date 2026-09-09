MATCH (c:Concept {uri: $uri})
OPTIONAL MATCH (c)-[r:HAS_ALT_LABEL]->(:Literal {type: 'concept_alt_label'})
DELETE r
WITH DISTINCT c
FOREACH (al IN $alt_labels |
  MERGE (l:Literal:Embeddable {value:    trim(al.value),
                    language: coalesce(nullif(trim(al.language), ''), 'und'),
                    type:     'concept_alt_label'})
  ON CREATE SET l.embedding_status = 'pending'
  MERGE (c)-[:HAS_ALT_LABEL]->(l)
)
