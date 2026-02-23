MERGE (c:Concept {uid: $uid})
  ON CREATE SET c.uri = $uri
WITH c, $pref_labels AS pref_labels, $alt_labels AS alt_labels, $document_uid AS document_uid

FOREACH (pref_label IN pref_labels |
  MERGE
    (l1:Literal {value: pref_label.value, language: coalesce(nullif(trim(pref_label.language), ''), 'und'),
                 type:  'concept_pref_label'})
  MERGE (c)-[:HAS_PREF_LABEL]->(l1)
)

FOREACH (alt_label IN alt_labels |
  MERGE
    (l2:Literal {value: alt_label.value, language: coalesce(nullif(trim(alt_label.language), ''), 'und'),
                 type:  'concept_alt_label'})
  MERGE (c)-[:HAS_ALT_LABEL]->(l2)
)

WITH c, document_uid
MATCH (d:Document {uid: document_uid})
MERGE (d)-[:HAS_SUBJECT]->(c)