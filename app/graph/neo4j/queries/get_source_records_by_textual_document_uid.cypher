MATCH (doc:TextualDocument {uid: $textual_document_uid})
MATCH (doc)-[:RECORDED_BY]->(s:SourceRecord)
OPTIONAL MATCH (s)-[:HAS_TITLE]->(t:Literal)
OPTIONAL MATCH (s)-[:HAS_ABSTRACT]->(a:Literal)
OPTIONAL MATCH (s)-[:HAS_IDENTIFIER]->(i:PublicationIdentifier)
OPTIONAL MATCH (s)-[:HARVESTED_FOR]->(p:Person)
OPTIONAL MATCH (s)-[:HAS_SUBJECT]->(c:Concept)
OPTIONAL MATCH (s)-[:PUBLISHED_IN]->(issue:SourceIssue)
OPTIONAL MATCH (issue)-[:ISSUED_BY]->(journal:SourceJournal)
OPTIONAL MATCH (journal)-[:HAS_IDENTIFIER]->(ji:JournalIdentifier)
RETURN s, issue, journal,
       collect(DISTINCT p.uid) AS harvested_for_uids,
       collect(DISTINCT t) AS titles,
       collect(DISTINCT i) AS identifiers,
       collect(DISTINCT a) AS abstracts,
       collect(DISTINCT c) AS subjects,
       collect(DISTINCT ji) AS journal_identifiers


