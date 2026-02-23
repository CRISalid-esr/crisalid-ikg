MATCH (concept:Concept {uri: $uri})
OPTIONAL MATCH (concept)-[:HAS_PREF_LABEL]->(pref_label:Literal {type: 'concept_pref_label'})
OPTIONAL MATCH (concept)-[:HAS_ALT_LABEL]->(alt_label:Literal {type: 'concept_alt_label'})
RETURN concept,
       collect(DISTINCT CASE
         WHEN pref_label IS NOT NULL
       THEN {value: pref_label.value, language: pref_label.language}
         END) AS pref_labels,
       collect(DISTINCT CASE
         WHEN alt_label IS NOT NULL
       THEN {value: alt_label.value, language: alt_label.language}
         END) AS alt_labels