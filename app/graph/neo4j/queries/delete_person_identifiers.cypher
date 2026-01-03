MATCH (p:Person {uid: $person_uid})-[r:HAS_IDENTIFIER]->(:AgentIdentifier)
  WHERE NOT (i.type IN $identifier_types AND i.value IN $identifier_values)
DELETE r;