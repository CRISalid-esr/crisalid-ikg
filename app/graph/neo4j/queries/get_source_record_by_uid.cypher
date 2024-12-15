MATCH (s:SourceRecord {uid: $source_record_uid})
OPTIONAL MATCH (s)-[:HAS_TITLE]->(t:Literal)
OPTIONAL MATCH (s)-[:HAS_ABSTRACT]->(a:Literal)
OPTIONAL MATCH (s)-[:HAS_IDENTIFIER]->(i:PublicationIdentifier)
OPTIONAL MATCH (s)-[:HARVESTED_FOR]->(p:Person)
OPTIONAL MATCH (s)-[:HAS_SUBJECT]->(c:Concept)
OPTIONAL MATCH (s)-[:HAS_CONTRIBUTION]->(sc:SourceContribution)
OPTIONAL MATCH (sc)-[:CONTRIBUTOR]->(contributor:SourcePerson)
OPTIONAL MATCH (s)-[:PUBLISHED_IN]->(issue:SourceIssue)
OPTIONAL MATCH (issue)-[:ISSUED_BY]->(journal:SourceJournal)
OPTIONAL MATCH (journal)-[:HAS_IDENTIFIER]->(ji:JournalIdentifier)
WITH s, issue, journal, t, a, i, p, c, ji,
     collect(DISTINCT t) AS titles,
     collect(DISTINCT i) AS identifiers,
     collect(DISTINCT a) AS abstracts,
     collect(DISTINCT p.uid) AS harvested_for_uids,
     collect(DISTINCT c) AS subjects,
     collect(DISTINCT ji) AS journal_identifiers,
     collect(DISTINCT sc { .*, contributor: contributor }) AS contributions
RETURN s, issue, journal,
       titles, identifiers, abstracts,
       harvested_for_uids, subjects, journal_identifiers,
       contributions
