MATCH (s:SourceJournal {uid: $uid})
OPTIONAL MATCH (s)-[r:HAS_IDENTIFIER]->(i:JournalIdentifier)
RETURN s,
       collect(i) AS identifiers
