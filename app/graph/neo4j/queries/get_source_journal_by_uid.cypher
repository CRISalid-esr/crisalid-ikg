MATCH (s:SourceJournal {uid: $uid})
MATCH (s)-[r:HAS_IDENTIFIER]->(i:JournalIdentifier)
RETURN s,
       collect(i) AS identifiers
