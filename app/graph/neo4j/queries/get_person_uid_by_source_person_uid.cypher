MATCH (sp:SourcePerson {uid: $source_person_uid})<-[:RECORDED_BY]-(person:Person {external: $external})
RETURN person.uid AS person_uid
LIMIT 1
