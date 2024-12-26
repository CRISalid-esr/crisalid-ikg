UNWIND $source_person_uids AS source_person_uid
MATCH (sp:SourcePerson {uid: source_person_uid})
OPTIONAL MATCH (sp)<-[rel:RECORDED_BY]-(:Person)
DELETE rel
WITH sp
MATCH (person:Person {uid: $person_uid})
MERGE (sp)<-[:RECORDED_BY]-(person)
