CREATE (p:Person {uid: $person_uid, display_name: $display_name, external: $external})
SET p.display_name_variants = $display_name_variants
WITH p

FOREACH (name IN $names |
  CREATE (pn:PersonName)
  CREATE (p)-[:HAS_NAME]->(pn)

  FOREACH (first_name IN name.first_names |
    MERGE (fn:Literal {
      value:    trim(first_name.value),
      language: coalesce(nullif(trim(first_name.language), ''), 'und'),
      type:     'person_first_name'
    })
    MERGE (pn)-[:HAS_FIRST_NAME]->(fn)
  )

  FOREACH (last_name IN name.last_names |
    MERGE (ln:Literal {
      value:    trim(last_name.value),
      language: coalesce(nullif(trim(last_name.language), ''), 'und'),
      type:     'person_last_name'
    })
    MERGE (pn)-[:HAS_LAST_NAME]->(ln)
  )
)

WITH p
UNWIND $identifiers AS identifier
CREATE (i:AgentIdentifier {type: identifier.type, value: identifier.value})
SET i.authenticated = CASE WHEN identifier.authenticated IS NOT NULL THEN identifier.authenticated
  ELSE i.authenticated
  END,
i.authentication_date = CASE WHEN identifier.authentication_date IS NOT NULL THEN identifier.authentication_date
  ELSE i.authentication_date
  END
CREATE (p)-[:HAS_IDENTIFIER]->(i)