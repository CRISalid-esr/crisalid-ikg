UNWIND $pref_labels AS pref_label
MATCH (:Concept {uri: $uri})-[r:HAS_PREF_LABEL]->(l:Literal {type: 'concept_pref_label'})
  WHERE l.value = pref_label.value
  AND l.language = coalesce(nullif(trim(pref_label.language), ''), 'und')
DELETE r;
