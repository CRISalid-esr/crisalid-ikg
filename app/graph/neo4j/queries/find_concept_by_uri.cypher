MATCH (concept:Concept {uri: $uri})
OPTIONAL MATCH (concept)-[:HAS_PREF_LABEL]->(pref_label:Literal)
OPTIONAL MATCH (concept)-[:HAS_ALT_LABEL]->(alt_label:Literal)
RETURN concept,
       collect(DISTINCT {value: pref_label.value, language: pref_label.language}) AS pref_labels,
       collect(DISTINCT {value: alt_label.value, language: alt_label.language}) AS alt_labels