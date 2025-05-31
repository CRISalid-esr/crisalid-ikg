MATCH (j:Journal {uid: $uid})
OPTIONAL MATCH (j)-[r:HAS_IDENTIFIER]->(i:JournalIdentifier)
RETURN j,
       collect(i) AS identifiers
