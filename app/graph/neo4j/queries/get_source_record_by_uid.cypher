MATCH (s:SourceRecord {uid: $source_record_uid})
OPTIONAL MATCH (s)-[:HAS_TITLE]->(t:Literal)
OPTIONAL MATCH (s)-[:HAS_ABSTRACT]->(a:Literal)
OPTIONAL MATCH (s)-[:HAS_IDENTIFIER]->(i:PublicationIdentifier)
OPTIONAL MATCH (s)-[:HARVESTED_FOR]->(p:Person)
OPTIONAL MATCH (s)-[:HAS_SUBJECT]->(c:Concept)
OPTIONAL MATCH (s)-[:PUBLISHED_IN]->(issue:SourceIssue)
OPTIONAL MATCH (issue)-[:ISSUED_BY]->(journal:SourceJournal)
OPTIONAL MATCH (journal)-[:HAS_IDENTIFIER]->(ji:JournalIdentifier)
RETURN s, issue, journal,
       collect(t) AS titles,
       collect(i) AS identifiers,
       collect(a) AS abstracts,
       collect(p) AS persons,
       collect(c) AS subjects,
       collect(DISTINCT ji) AS journal_identifiers




