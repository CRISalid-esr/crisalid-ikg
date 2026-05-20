CALL apoc.create.node($labels, $properties) YIELD node AS org
WITH org

FOREACH (sl IN $short_labels |
  MERGE (l:Literal {
    value: trim(sl.value),
    language: coalesce(nullif(trim(sl.language), ''), 'und'),
    type: "organization_short_label"
  })
  MERGE (org)-[:HAS_SHORT_LABEL]->(l)
)

WITH org
FOREACH (ll IN $long_labels |
  MERGE (l:Literal {
    value: trim(ll.value),
    language: coalesce(nullif(trim(ll.language), ''), 'und'),
    type: "organization_long_label"
  })
  MERGE (org)-[:HAS_LONG_LABEL]->(l)
)

WITH org
FOREACH (lt IN $local_types |
  MERGE (l:Literal {
    value: trim(lt.value),
    language: coalesce(nullif(trim(lt.language), ''), 'und'),
    type: "organization_local_type"
  })
  MERGE (org)-[:HAS_LOCAL_TYPE]->(l)
)

WITH org
FOREACH (d IN $descriptions |
  MERGE (t:TextLiteral {key: d.key, type: "organization_description"})
  ON CREATE SET t.value = d.value,
               t.language = coalesce(nullif(trim(d.language), ''), 'und')
  MERGE (org)-[:HAS_DESCRIPTION]->(t)
)

WITH org
FOREACH (i IN $identifiers |
  MERGE (ai:AgentIdentifier {type: i.type, value: i.value})
  MERGE (org)-[:HAS_IDENTIFIER]->(ai)
)

RETURN org.uid AS uid
