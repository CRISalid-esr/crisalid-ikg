UNWIND $source_person_uids AS source_person_uid
MATCH (p:Person {uid: $person_uid})-[rb:RECORDED_BY]->(sp:SourcePerson {uid: source_person_uid})
WHERE NOT EXISTS {
  MATCH (sp)<-[:CONTRIBUTOR]-(:SourceContribution)<-[:HAS_CONTRIBUTION]-(other:SourceRecord)-[:HARVESTED_FOR]->(p)
  WHERE other.uid <> $source_record_uid
}
DELETE rb
