UNWIND $source_person_uids AS source_person_uid
MATCH (sp:SourcePerson {uid: source_person_uid})
MATCH (person:Person {uid: $person_uid})
MERGE (sp)<-[:RECORDED_BY]-(person)
