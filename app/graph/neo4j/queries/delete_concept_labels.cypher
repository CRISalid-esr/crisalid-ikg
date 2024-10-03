MATCH (c:Concept {uri: $uri})-[r:HAS_PREF_LABEL|HAS_ALT_LABEL]->(l:Literal)
DELETE r, l
