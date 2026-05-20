MATCH (o:OrganizationUnit {uid: $uid})
FOREACH (sl IN $short_labels |
  MERGE (l:Literal {
    value: trim(sl.value),
    language: coalesce(nullif(trim(sl.language), ''), 'und'),
    type: "organization_short_label"
  })
  MERGE (o)-[:HAS_SHORT_LABEL]->(l)
)
WITH o
FOREACH (ll IN $long_labels |
  MERGE (l:Literal {
    value: trim(ll.value),
    language: coalesce(nullif(trim(ll.language), ''), 'und'),
    type: "organization_long_label"
  })
  MERGE (o)-[:HAS_LONG_LABEL]->(l)
)
WITH o
FOREACH (lt IN $local_types |
  MERGE (l:Literal {
    value: trim(lt.value),
    language: coalesce(nullif(trim(lt.language), ''), 'und'),
    type: "organization_local_type"
  })
  MERGE (o)-[:HAS_LOCAL_TYPE]->(l)
)
WITH o
FOREACH (d IN $descriptions |
  MERGE (t:TextLiteral {key: d.key, type: "organization_description"})
  ON CREATE SET t.value = d.value,
               t.language = coalesce(nullif(trim(d.language), ''), 'und')
  MERGE (o)-[:HAS_DESCRIPTION]->(t)
)
