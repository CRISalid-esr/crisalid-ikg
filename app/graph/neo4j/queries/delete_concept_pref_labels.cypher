UNWIND $pref_labels AS pref_label
MATCH (:Concept {uri: $uri})-[r:HAS_PREF_LABEL]->(l:Literal)
WHERE l.value=pref_label.value AND (l.language=pref_label.language OR (l.language is NULL and pref_label.language IS NULL))
DELETE r, l