UNWIND $alt_labels AS alt_label
MATCH (c:Concept {uri: $uri})-[r:HAS_ALT_LABEL]->(l:Literal {type: 'concept_alt_label'})
  WHERE l.value = alt_label.value
  AND l.language = coalesce(nullif(trim(alt_label.language), ''), 'und')
DELETE r;
