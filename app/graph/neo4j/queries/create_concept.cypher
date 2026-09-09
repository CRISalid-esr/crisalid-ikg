CREATE (c:Concept {uid: $uid, uri: $uri})
WITH c

UNWIND $pref_labels AS pref_label
MERGE (pl:Literal:Embeddable {
  value:    trim(pref_label.value),
  language: coalesce(nullif(trim(pref_label.language), ''), 'und'),
  type:     'concept_pref_label'
})
ON CREATE SET pl.embedding_status = 'pending'
MERGE (c)-[:HAS_PREF_LABEL]->(pl)

WITH c

UNWIND $alt_labels AS alt_label
MERGE (al:Literal:Embeddable {
  value:    trim(alt_label.value),
  language: coalesce(nullif(trim(alt_label.language), ''), 'und'),
  type:     'concept_alt_label'
})
ON CREATE SET al.embedding_status = 'pending'
MERGE (c)-[:HAS_ALT_LABEL]->(al);
