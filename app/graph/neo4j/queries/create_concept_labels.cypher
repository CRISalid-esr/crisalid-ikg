MATCH (c:Concept {uid: $uid})

FOREACH (pref_label IN $pref_labels |
  MERGE
    (l:Literal:Embeddable {value: pref_label.value, language: coalesce(nullif(trim(pref_label.language), ''), 'und'),
                type:  'concept_pref_label'})
  ON CREATE SET l.embedding_status = 'pending'
  MERGE (c)-[:HAS_PREF_LABEL]->(l)
)

FOREACH (alt_label IN $alt_labels |
  MERGE
    (l:Literal:Embeddable {value: alt_label.value, language: coalesce(nullif(trim(alt_label.language), ''), 'und'),
                type:  'concept_alt_label'})
  ON CREATE SET l.embedding_status = 'pending'
  MERGE (c)-[:HAS_ALT_LABEL]->(l)
)
