MATCH (d:Document)-[:HAS_CONTRIBUTION]->(contribution:Contribution)<-[:HAS_CONTRIBUTION]-(contributor:Person {uid: $person_uid})
RETURN collect(d.uid) AS document_uids
