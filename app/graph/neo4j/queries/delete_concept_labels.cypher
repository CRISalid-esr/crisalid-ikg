MATCH (c:Concept {uri: $uri})-[r:HAS_PREF_LABEL]->(l:Literal)
WHERE l.value IN [label IN $pref_labels | label.value] AND l.language IN [label IN $pref_labels | label.language]
DELETE r, l

WITH c
MATCH (c)-[r:HAS_ALT_LABEL]->(l:Literal)
WHERE l.value IN [label IN $alt_labels | label.value] AND l.language IN [label IN $alt_labels | label.language]
DELETE r, l