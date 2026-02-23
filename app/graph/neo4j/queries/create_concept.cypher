CREATE (c:Concept {uid: $uid, uri: $uri})
WITH c

UNWIND $pref_labels AS pref_label
MERGE (pl:Literal {
  value:    trim(pref_label.value),
  language: coalesce(nullif(trim(pref_label.language), ''), 'und'),
  type:     'concept_pref_label'
})
MERGE (c)-[:HAS_PREF_LABEL]->(pl)

WITH c

UNWIND $alt_labels AS alt_label
MERGE (al:Literal {
  value:    trim(alt_label.value),
  language: coalesce(nullif(trim(alt_label.language), ''), 'und'),
  type:     'concept_alt_label'
})
MERGE (c)-[:HAS_ALT_LABEL]->(al);
