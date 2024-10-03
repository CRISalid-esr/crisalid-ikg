MATCH (concept:Concept {uri: $uri})
OPTIONAL MATCH (concept)-[:HAS_PREF_LABEL]->(pref_label:Literal)
OPTIONAL MATCH (concept)-[:HAS_ALT_LABEL]->(alt_label:Literal)
RETURN concept,
       collect(DISTINCT CASE
         WHEN pref_label IS NOT NULL
       THEN {value: pref_label.value, language: pref_label.language}
         ELSE null
         END) AS pref_labels,
       collect(DISTINCT CASE
         WHEN alt_label IS NOT NULL
       THEN {value: alt_label.value, language: alt_label.language}
         ELSE null
         END) AS alt_labels