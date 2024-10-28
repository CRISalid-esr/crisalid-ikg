MATCH (c:Concept {uri: $uri})

FOREACH (pref_label IN $pref_labels |
    CREATE (c)-[:HAS_PREF_LABEL]->(:Literal {value: pref_label.value, language: pref_label.language})
)

FOREACH (alt_label IN $alt_labels |
    CREATE (c)-[:HAS_ALT_LABEL]->(:Literal {value: alt_label.value, language: alt_label.language})
)
