CREATE (c:Concept {uri: $uri})
WITH c
UNWIND $pref_labels AS pref_label
CREATE (c)-[:HAS_PREF_LABEL]->(:Literal {value: pref_label.value, language: pref_label.language})
WITH c, count(pref_label) AS pref_label_count
UNWIND $alt_labels AS alt_label
CREATE (c)-[:HAS_ALT_LABEL]->(:Literal {value: alt_label.value, language: alt_label.language})
