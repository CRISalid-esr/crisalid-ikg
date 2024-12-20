MATCH (s:SourcePerson {uid: $uid})
OPTIONAL MATCH (s)-[r:HAS_IDENTIFIER]->(i:SourcePersonIdentifier)
RETURN s,
       collect(i) AS identifiers