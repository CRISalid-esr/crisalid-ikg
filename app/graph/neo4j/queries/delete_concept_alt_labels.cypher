UNWIND $alt_labels AS alt_label
MATCH (:Concept {uri: $uri})-[r:HAS_ALT_LABEL]->(l:Literal)
WHERE l.value=alt_label.value AND (l.language=alt_label.language OR (l.language is NULL and alt_label.language IS NULL))
DETACH DELETE l