MATCH (p:Person {uid: $person_uid})
UNWIND $identifiers AS identifier
MERGE (i:AgentIdentifier {type: identifier.type, value: identifier.value})
  ON CREATE SET
    i.type = identifier.type,
    i.value = identifier.value,
    i.validated = CASE
      WHEN identifier.validated = true OR identifier.authenticated = true THEN true
      ELSE false
    END,
    i.authenticated = CASE
      WHEN identifier.authenticated = true THEN true
      ELSE false
    END,
    i.authentication_date = CASE
      WHEN identifier.authenticated = true
        AND identifier.authentication_date IS NOT NULL
      THEN identifier.authentication_date
      ELSE NULL
    END
  ON MATCH SET
    i.type = identifier.type,
    i.value = identifier.value,
    i.validated = CASE
      WHEN identifier.validated = true OR identifier.authenticated = true THEN true
      ELSE coalesce(i.validated, false)
    END,
    i.authenticated = CASE
      WHEN identifier.authenticated = true THEN true
      ELSE coalesce(i.authenticated, false)
    END,
    i.authentication_date = CASE
      WHEN identifier.authenticated = true
        AND identifier.authentication_date IS NOT NULL
      THEN identifier.authentication_date
      ELSE i.authentication_date
    END

MERGE (p)-[:HAS_IDENTIFIER]->(i)