MATCH (c:Concept {uri: $uri})
OPTIONAL MATCH (c)-[r:HAS_DEFINITION]->(:Literal {type: 'concept_definition'})
DELETE r
WITH DISTINCT c
FOREACH (def IN CASE WHEN $definition IS NOT NULL THEN [$definition] ELSE [] END |
  MERGE (l:Literal {value:    trim(def.value),
                    language: coalesce(nullif(trim(def.language), ''), 'und'),
                    type:     'concept_definition'})
  MERGE (c)-[:HAS_DEFINITION]->(l)
)
