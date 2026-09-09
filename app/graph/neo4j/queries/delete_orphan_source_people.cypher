UNWIND $source_person_uids AS source_person_uid
MATCH (sp:SourcePerson {uid: source_person_uid})
WHERE NOT (sp)<-[:CONTRIBUTOR]-(:SourceContribution)
OPTIONAL MATCH (sp)-[:HAS_IDENTIFIER]->(spi:SourcePersonIdentifier)
WITH sp, collect(spi) AS identifiers
DETACH DELETE sp
WITH identifiers
UNWIND identifiers AS spi
WITH spi
WHERE NOT (spi)<-[:HAS_IDENTIFIER]-(:SourcePerson)
DELETE spi
