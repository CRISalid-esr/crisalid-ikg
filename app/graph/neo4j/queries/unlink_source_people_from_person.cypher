UNWIND $source_person_uids AS source_person_uid
MATCH (sp:SourcePerson {uid: source_person_uid})
MATCH (sp)<-[rel:RECORDED_BY]-(old:Person {external: true})
WHERE NOT old.uid = $person_to_preserve_uid
DELETE rel
WITH sp, old
OPTIONAL MATCH (old)-[hc:HAS_CONTRIBUTION]->(contribution:Contribution)
  WHERE NOT EXISTS((old)-[:RECORDED_BY]->(:SourcePerson))
DETACH DELETE hc, contribution, old