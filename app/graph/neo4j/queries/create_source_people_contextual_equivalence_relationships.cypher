UNWIND $source_people_couples AS couple
MATCH (n1:SourcePerson {uid: couple[0]})<-[:CONTRIBUTOR]-(c1:SourceContribution)<-[:HAS_CONTRIBUTION]-(sr1:SourceRecord)<-[:RECORDED_BY]-(d:Document {uid: $document_uid})
MATCH (n2:SourcePerson {uid: couple[1]})<-[:CONTRIBUTOR]-(c2:SourceContribution)<-[:HAS_CONTRIBUTION]-(sr2:SourceRecord)<-[:RECORDED_BY]-(d)
MERGE (n1)-[:CONTEXTUAL_EQUIVALENT {contextUid: $document_uid}]->(n2)
MERGE (c1)-[:CONTEXTUAL_EQUIVALENT {contextUid: $document_uid}]->(c2)
