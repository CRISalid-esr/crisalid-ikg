MATCH (i:Institution {uid: $uid})
WITH i

FOREACH (name_data IN CASE WHEN size($names) > 0 THEN $names ELSE [] END |
  MERGE (n:Literal:Embeddable {
    value: trim(name_data.value),
    language: coalesce(nullif(trim(name_data.language), ''), 'und'),
    type: 'institution_name'
  })
  ON CREATE SET n.embedding_status = 'pending'
  MERGE (i)-[:HAS_NAME]->(n)
)

RETURN i;
