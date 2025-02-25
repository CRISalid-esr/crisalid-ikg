MATCH (s:SourceRecord {uid: $source_record_uid})
OPTIONAL MATCH (s)-[:HAS_TITLE]->(title:Literal)
OPTIONAL MATCH (s)-[:HAS_ABSTRACT]->(abstract:Literal)
OPTIONAL MATCH (s)-[:HAS_IDENTIFIER]->(pub_identifier:PublicationIdentifier)
OPTIONAL MATCH (s)-[:HARVESTED_FOR]->(person:Person)
OPTIONAL MATCH (s)-[:HAS_SUBJECT]->(concept:Concept)
OPTIONAL MATCH (s)-[:PUBLISHED_IN]->(issue:SourceIssue)
OPTIONAL MATCH (issue)-[:ISSUED_BY]->(journal:SourceJournal)
OPTIONAL MATCH (journal)-[:HAS_IDENTIFIER]->(journ_identifier:JournalIdentifier)
OPTIONAL MATCH (s)-[:HAS_CONTRIBUTION]->(contribution:SourceContribution)
OPTIONAL MATCH (contribution)-[:CONTRIBUTOR]->(contributor:SourcePerson)
OPTIONAL MATCH (contributor)-[:HAS_IDENTIFIER]->(pers_identifier:SourcePersonIdentifier)
OPTIONAL MATCH (contribution)-[:HAS_AFFILIATION]->(organization:SourceOrganization)
OPTIONAL MATCH (organization)-[:HAS_IDENTIFIER]->(org_identifier:SourceOrganizationIdentifier)

WITH DISTINCT s, contribution, contributor, person, title, pub_identifier, abstract, concept, issue, journal, journ_identifier,
              organization, org_identifier, pers_identifier

WITH DISTINCT s, contribution, contributor, person, title, pub_identifier, abstract, concept, issue, journal, journ_identifier,
              organization, pers_identifier, collect(DISTINCT org_identifier) AS org_identifiers

WITH DISTINCT s, contribution, contributor, person, title, pub_identifier, abstract, concept, issue, journal, journ_identifier,
              collect(organization {.*, identifiers: org_identifiers}) AS affiliations, collect(DISTINCT pers_identifier) AS pers_identifiers

WITH DISTINCT s, contribution, contributor, person, title, pub_identifier, abstract, concept, issue, journal, journ_identifier,
              affiliations, contributor {.*, identifiers: pers_identifiers } AS contributor_with_identifiers

WITH DISTINCT s, person, title, pub_identifier, abstract, concept, issue, journal, journ_identifier,
     collect(contribution {.*, contributor: contributor_with_identifiers, affiliations: affiliations}) AS contributions

RETURN DISTINCT s, issue, journal,
       collect(DISTINCT person.uid) AS harvested_for_uids,
       collect(DISTINCT title) AS titles,
       collect(DISTINCT pub_identifier) AS identifiers,
       collect(DISTINCT abstract) AS abstracts,
       collect(DISTINCT concept) AS subjects,
       collect(DISTINCT journ_identifier) AS journal_identifiers,
       contributions



