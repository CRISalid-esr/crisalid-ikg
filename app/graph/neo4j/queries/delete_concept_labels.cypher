MATCH (c:Concept {uid: $uid})

FOREACH (pl IN CASE WHEN size($pref_labels) > 0 THEN $pref_labels ELSE [] END |
  MATCH (c)-[r1:HAS_PREF_LABEL]->(l1:Literal {type: 'concept_pref_label'})
  WHERE l1.value = pl.value
    AND l1.language = coalesce(nullif(trim(pl.language), ''), 'und')
  DELETE r1
)

FOREACH (al IN CASE WHEN size($alt_labels) > 0 THEN $alt_labels ELSE [] END |
  MATCH (c)-[r2:HAS_ALT_LABEL]->(l2:Literal {type: 'concept_alt_label'})
  WHERE l2.value = al.value
    AND l2.language = coalesce(nullif(trim(al.language), ''), 'und')
  DELETE r2
);
